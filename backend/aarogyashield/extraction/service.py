from __future__ import annotations

import hashlib
import uuid
from datetime import timezone
from typing import Any

from .images import sanitize_image
from .ports import InvalidProviderResponse, ProviderError
from .provider import validate_result


class ExtractionError(Exception):
    def __init__(self, code: str, status: int, message: str):
        self.code, self.status, self.message = code, status, message
        super().__init__(message)


def create_draft(*, actor: dict[str, Any], patient_id: str, encounter_id: str,
                 image_bytes: bytes, mime_type: str, ports: Any) -> dict[str, Any]:
    if actor.get("role") != "admin":
        raise ExtractionError("ROLE_NOT_ALLOWED", 403, "Administrator role required.")
    clean, clean_type = sanitize_image(image_bytes, mime_type, getattr(ports, "image_max_bytes", 5 * 1024 * 1024))
    request_id = str(uuid.uuid4())
    # Validate reviewer-selected bindings before a potentially billable provider call.
    with ports.uow_factory(patient_id=patient_id) as uow:
        patient = uow.get_patient(patient_id)
        encounter = uow.get_encounter(encounter_id)
        if patient is None or encounter is None or encounter.get("patient_id") != patient_id:
            raise ExtractionError("NOT_FOUND", 404, "Patient or encounter not found.")
    try:
        result = ports.provider.extract(clean, clean_type, request_id)
        proposed = validate_result(result.get("proposed_json"))
    except InvalidProviderResponse as exc:
        raise ExtractionError("PROVIDER_INVALID_RESPONSE", 502, "Extraction provider returned an invalid response.") from exc
    except ProviderError as exc:
        raise ExtractionError("PROVIDER_UNAVAILABLE", 503, "Extraction provider unavailable.") from exc
    except Exception as exc:
        # Provider adapters are required to translate upstream errors into ProviderError.
        raise ExtractionError("PROVIDER_UNAVAILABLE", 503, "Extraction provider unavailable.") from exc
    if result.get("source_mode") not in {"live", "fixture"}:
        raise ExtractionError("PROVIDER_INVALID_RESPONSE", 502, "Extraction provider returned an invalid response.")
    model_id = result.get("model_id")
    prompt_version = result.get("prompt_version")
    if not isinstance(model_id, str) or not model_id or len(model_id) > 200 or not isinstance(prompt_version, str):
        raise ExtractionError("PROVIDER_INVALID_RESPONSE", 502, "Extraction provider returned an invalid response.")
    warnings = result.get("warnings", [])
    if not isinstance(warnings, list) or any(not isinstance(w, str) or len(w) > 500 for w in warnings):
        raise ExtractionError("PROVIDER_INVALID_RESPONSE", 502, "Extraction provider returned an invalid response.")
    timestamp = ports.now()
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise RuntimeError("ports.now must return an aware datetime")
    with ports.uow_factory(patient_id=patient_id) as uow:
        patient = uow.get_patient(patient_id)
        encounter = uow.get_encounter(encounter_id)
        if patient is None or encounter is None or encounter.get("patient_id") != patient_id:
            raise ExtractionError("NOT_FOUND", 404, "Patient or encounter not found.")
        draft = {
            "id": str(uuid.uuid4()), "version": 1, "patient_id": patient_id,
            "encounter_id": encounter_id, "state": "draft",
            "image_sha256": hashlib.sha256(clean).hexdigest(), "model_id": model_id,
            "prompt_version": prompt_version, "source_mode": result["source_mode"],
            "proposed_json": proposed, "warnings": warnings,
            "suggested_category": "restricted", "created_at": timestamp.astimezone(timezone.utc),
            "created_by": actor.get("id"),
        }
        stored = uow.insert_draft(draft)
        uow.append_audit({"occurred_at": timestamp, "actor_id": actor.get("id"),
                          "patient_id": patient_id, "action": "extraction.drafted",
                          "encounter_id": encounter_id, "purpose": None, "categories": [],
                          "decision": "SUCCESS", "consent_id": None, "policy_version": None,
                          "request_id": request_id})
    # Ensure no reference to the uploaded/sanitized image escapes this method.
    del clean, image_bytes
    return stored
