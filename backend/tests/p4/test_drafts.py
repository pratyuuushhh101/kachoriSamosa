from fastapi import FastAPI
from fastapi.testclient import TestClient

import pytest

from aarogyashield.extraction.images import ImageInputError
from aarogyashield.extraction.ports import ProviderError
from aarogyashield.extraction.router import create_router
from aarogyashield.extraction.service import ExtractionError, create_draft
from conftest import FakeProvider, png_bytes


def test_draft_binds_selected_patient_and_encounter_and_stores_hash(harness):
    uow, ports = harness
    row = create_draft(actor={"id": "a-demo-1", "role": "admin"}, patient_id="p-demo-1", encounter_id="E1", image_bytes=png_bytes(), mime_type="image/png", ports=ports)
    assert row["patient_id"] == "p-demo-1" and row["encounter_id"] == "E1"
    assert row["suggested_category"] == "restricted" and len(row["image_sha256"]) == 64
    assert len(uow.drafts) == len(uow.audit) == 1


def test_non_admin_rejected_before_provider(harness):
    _, ports = harness
    with pytest.raises(ExtractionError):
        create_draft(actor={"role": "dentist"}, patient_id="p-demo-1", encounter_id="E1", image_bytes=png_bytes(), mime_type="image/png", ports=ports)
    assert not ports.provider.calls


def test_invalid_encounter_persists_nothing(harness):
    uow, ports = harness
    with pytest.raises(ExtractionError):
        create_draft(actor={"id": "a-demo-1", "role": "admin"}, patient_id="p-demo-1", encounter_id="E2", image_bytes=png_bytes(), mime_type="image/png", ports=ports)
    assert not uow.drafts and not uow.audit


def test_provider_timeout_no_consent_change(harness):
    uow, ports = harness
    ports.provider = FakeProvider(error=ProviderError("provider unavailable"))
    with pytest.raises(ExtractionError):
        create_draft(actor={"id": "a-demo-1", "role": "admin"}, patient_id="p-demo-1", encounter_id="E1", image_bytes=png_bytes(), mime_type="image/png", ports=ports)
    assert not uow.drafts and not uow.audit


def test_image_instruction_cannot_publish(harness):
    uow, ports = harness
    row = create_draft(actor={"id": "a-demo-1", "role": "admin"}, patient_id="p-demo-1", encounter_id="E1", image_bytes=png_bytes(), mime_type="image/png", ports=ports)
    assert row["state"] == "draft" and not hasattr(uow, "resources")


def test_upload_route_requires_admin_and_marks_response_private(harness):
    _, ports = harness
    ports.current_actor = lambda: {"id": "a-demo-1", "role": "admin", "session_id": "s1"}
    ports.require_csrf = lambda: None
    app = FastAPI(); app.include_router(create_router(ports))
    response = TestClient(app).post("/api/extraction-drafts", data={"patient_id": "p-demo-1", "encounter_id": "E1"}, files={"image": ("synthetic.png", png_bytes(), "image/png")})
    assert response.status_code == 201
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["source_mode"] == "fixture"


def test_upload_route_rejects_non_admin_before_provider(harness):
    _, ports = harness
    ports.current_actor = lambda: {"id": "d-demo-1", "role": "dentist", "session_id": "s1"}
    ports.require_csrf = lambda: None
    app = FastAPI(); app.include_router(create_router(ports))
    response = TestClient(app).post("/api/extraction-drafts", data={"patient_id": "p-demo-1", "encounter_id": "E1"}, files={"image": ("synthetic.png", png_bytes(), "image/png")})
    assert response.status_code == 403
    assert not ports.provider.calls
