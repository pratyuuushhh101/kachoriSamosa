import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from aarogyashield.extraction.confirmation import confirm_draft
from aarogyashield.extraction.router import create_router
from aarogyashield.extraction.schemas import ConfirmRequest
from aarogyashield.extraction.service import ExtractionError, create_draft
from conftest import png_bytes

ADMIN = {"id": "a-demo-1", "role": "admin"}


def proposal(**changes):
    data = {
        "document_type": "referral", "encounter_hint": "dental referral",
        "dental_summary": "Synthetic referral for tooth pain", "medication_mentions": [],
        "allergy_mentions": [], "sensitive_mentions": [], "uncertain_fields": [],
        "evidence_spans": [],
    }
    data.update(changes)
    return data


def request(**changes):
    data = {
        "expected_version": 1, "corrected_json": proposal(),
        "resource_summary": "Reviewed synthetic referral for tooth pain",
        "approved_category": "dental", "human_reviewed": True, "category_reviewed": True,
    }
    data.update(changes)
    return ConfirmRequest.model_validate(data)


def draft(harness):
    uow, ports = harness
    row = create_draft(actor=ADMIN, patient_id="p-demo-1", encounter_id="E1",
                       image_bytes=png_bytes(), mime_type="image/png", ports=ports)
    return uow, ports, row


def confirm(ports, row, body, actor=ADMIN):
    return confirm_draft(actor=actor, draft_id=row["id"], request=body,
                         uow_factory=ports.uow_factory, now=ports.now)


def test_unconfirmed_draft_not_in_chart(harness):
    uow, _, row = draft(harness)
    assert row["state"] == "draft"
    assert uow.resources == []


def test_non_reviewer_denied(harness):
    _, ports, row = draft(harness)
    with pytest.raises(ExtractionError) as error:
        confirm(ports, row, request(), actor={"id": "d-demo-1", "role": "dentist"})
    assert error.value.status == 403


def test_cross_patient_binding_denied(harness):
    uow, ports, row = draft(harness)
    # Simulate corrupted/mismatched persistence metadata; the locked encounter check must deny it.
    row["encounter_id"] = "E2"
    with pytest.raises(ExtractionError) as error:
        confirm(ports, row, request())
    assert error.value.status == 404
    assert not uow.resources


def test_uncertain_shared_category_denied_restricted_is_allowed(harness):
    uow, ports, row = draft(harness)
    uncertain = request(corrected_json=proposal(uncertain_fields=["dental_summary"]))
    with pytest.raises(ExtractionError) as error:
        confirm(ports, row, uncertain)
    assert error.value.status == 422
    restricted = request(corrected_json=proposal(uncertain_fields=["dental_summary"]),
                         approved_category="restricted", category_reviewed=False)
    result, retried = confirm(ports, row, restricted)
    assert result["category"] == "restricted" and not retried
    assert uow.resources[0]["category"] == "restricted"


def test_only_approved_summary_published(harness):
    uow, ports, row = draft(harness)
    body = request(corrected_json=proposal(allergy_mentions=["synthetic mention"], evidence_spans=[{"field": "allergy_mentions", "text": "synthetic mention"}], sensitive_mentions=["admin only"]))
    confirm(ports, row, body)
    resource = uow.resources[0]
    assert resource["summary"] == body.resource_summary
    assert set(resource) == {"id", "patient_id", "encounter_id", "category", "summary", "reviewed_at", "source_draft_id"}
    assert "evidence_spans" not in resource and "sensitive_mentions" not in resource


def test_confirmation_retry_one_resource_one_event(harness):
    uow, ports, row = draft(harness)
    body = request()
    first, retried = confirm(ports, row, body)
    second, retried_again = confirm(ports, row, body)
    assert not retried and retried_again
    assert first == second
    assert len(uow.resources) == 1 and len(uow.audit) == 2  # one draft event plus one confirmation event


def test_changed_retry_conflict(harness):
    _, ports, row = draft(harness)
    confirm(ports, row, request())
    with pytest.raises(ExtractionError) as error:
        confirm(ports, row, request(resource_summary="Changed reviewer summary"))
    assert error.value.status == 409


def test_audit_failure_rolls_back_resource_and_confirmation(harness):
    uow, ports, row = draft(harness)
    uow.fail_audit = True
    with pytest.raises(RuntimeError):
        confirm(ports, row, request())
    assert uow.resources == []
    assert row["state"] == "draft"


def test_confirmation_endpoint_returns_201_then_exact_retry_200(harness):
    _, ports = harness
    ports.current_actor = lambda: ADMIN
    ports.require_csrf = lambda: None
    client = TestClient(FastAPI())
    client.app.include_router(create_router(ports))
    request_body = request().model_dump(mode="json")
    # Seed the draft through the upload endpoint to exercise both feature routes together.
    uploaded = client.post("/api/extraction-drafts", data={"patient_id": "p-demo-1", "encounter_id": "E1"}, files={"image": ("synthetic.png", png_bytes(), "image/png")})
    draft_id = uploaded.json()["id"]
    first = client.post(f"/api/extraction-drafts/{draft_id}/confirm", json=request_body)
    second = client.post(f"/api/extraction-drafts/{draft_id}/confirm", json=request_body)
    assert first.status_code == 201 and second.status_code == 200
    assert first.headers["cache-control"] == "no-store"
    assert first.json() == second.json()
