from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

FIXTURES = Path(__file__).parents[3] / "fixtures" / "referrals"


def png_bytes(color=(255, 255, 255), size=(128, 80)):
    image = Image.new("RGB", size, color)
    out = BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


class FakeUow:
    def __init__(self):
        self.drafts, self.audit, self.resources = [], [], []
        self.scopes = []
        self.fail_audit = False
    def get_patient(self, patient_id):
        return {"id": patient_id} if patient_id in {"p-demo-1", "p-demo-2"} else None
    def get_encounter(self, encounter_id):
        return {"id": encounter_id, "patient_id": {"E1": "p-demo-1", "E2": "p-demo-2"}.get(encounter_id)}
    def insert_draft(self, row):
        self.drafts.append(row)
        return row
    def append_audit(self, event):
        if self.fail_audit:
            raise RuntimeError("audit unavailable")
        self.audit.append(event)
        return {**event, "id": f"audit-{len(self.audit)}"}
    def get_draft(self, draft_id):
        row = next((draft for draft in self.drafts if draft["id"] == draft_id), None)
        if row is None:
            return None
        if self.scopes and self.scopes[-1] is None:
            return {key: row[key] for key in ("id", "patient_id", "encounter_id", "created_by")}
        if self.scopes and row["patient_id"] != self.scopes[-1]:
            return None
        return row
    def insert_resource(self, row):
        if any(existing["source_draft_id"] == row["source_draft_id"] for existing in self.resources):
            raise RuntimeError("duplicate source draft")
        self.resources.append(row)
        return row
    def confirm_draft(self, draft_id, confirmation_hash, response_json, corrected_json, reviewer_id, confirmed_at):
        row = next(draft for draft in self.drafts if draft["id"] == draft_id)
        row.update(state="confirmed", confirmation_hash=confirmation_hash,
                   confirmation_response=deepcopy(response_json), corrected_json=deepcopy(corrected_json),
                   reviewer_id=reviewer_id, confirmed_at=confirmed_at)
        return row


class FakeProvider:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, []
    def extract(self, image_bytes, mime_type, request_id):
        self.calls.append((image_bytes, mime_type, request_id))
        if self.error:
            raise self.error
        return self.result or {
            "model_id": "fake-model", "prompt_version": "referral-extract-1", "source_mode": "fixture",
            "proposed_json": {"document_type": "referral", "encounter_hint": "dental referral", "dental_summary": "Synthetic tooth pain", "medication_mentions": [], "allergy_mentions": [], "sensitive_mentions": [], "uncertain_fields": [], "evidence_spans": []},
            "warnings": [],
        }


@pytest.fixture
def harness():
    uow = FakeUow()
    @contextmanager
    def factory(**kwargs):
        scope = kwargs.get("patient_id")
        uow.scopes.append(scope)
        snapshot = deepcopy((uow.drafts, uow.audit, uow.resources))
        try:
            yield uow
        except Exception:
            uow.drafts, uow.audit, uow.resources = snapshot
            raise
        finally:
            uow.scopes.pop()
    ports = SimpleNamespace(provider=FakeProvider(), uow_factory=factory,
                            now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
                            image_max_bytes=5 * 1024 * 1024, ai_mode="fixture")
    return uow, ports
