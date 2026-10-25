from contextlib import contextmanager
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
        self.drafts, self.audit = [], []
    def get_patient(self, patient_id):
        return {"id": patient_id} if patient_id in {"p-demo-1", "p-demo-2"} else None
    def get_encounter(self, encounter_id):
        return {"id": encounter_id, "patient_id": {"E1": "p-demo-1", "E2": "p-demo-2"}.get(encounter_id)}
    def insert_draft(self, row):
        self.drafts.append(row)
        return row
    def append_audit(self, event):
        self.audit.append(event)


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
        yield uow
    ports = SimpleNamespace(provider=FakeProvider(), uow_factory=factory,
                            now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
                            image_max_bytes=5 * 1024 * 1024, ai_mode="fixture")
    return uow, ports
