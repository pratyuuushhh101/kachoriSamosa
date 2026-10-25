from __future__ import annotations

import hashlib
import json
import uuid
from datetime import timezone
from typing import Any

from .schemas import ConfirmRequest, ConfirmationResponse
from .service import ExtractionError


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def confirm_draft(*, actor: dict[str, Any], draft_id: str, request: ConfirmRequest,
                  uow_factory: Any, now: Any) -> tuple[dict[str, Any], bool]:
    """Confirm a draft and publish one reviewed resource in the same UOW."""
    if actor.get("role") != "admin" or not actor.get("id"):
        raise ExtractionError("ROLE_NOT_ALLOWED", 403, "Administrator reviewer required.")
    if not request.human_reviewed:
        raise ExtractionError("REVIEW_REQUIRED", 422, "Explicit human review is required.")
    if request.approved_category in {"dental", "safety_summary"} and (
        not request.category_reviewed or request.corrected_json.uncertain_fields
    ):
        raise ExtractionError("CATEGORY_REVIEW_REQUIRED", 422, "Resolve uncertainty and review the category, or choose restricted.")

    # Resolve only safe ownership metadata before acquiring the patient lock.
    with uow_factory(patient_id=None) as metadata_uow:
        metadata = metadata_uow.get_draft(draft_id)
    if metadata is None:
        raise ExtractionError("NOT_FOUND", 404, "Draft not found.")
    patient_id = metadata.get("patient_id")
    encounter_id = metadata.get("encounter_id")
    if not isinstance(patient_id, str) or not isinstance(encounter_id, str):
        raise ExtractionError("NOT_FOUND", 404, "Draft not found.")

    payload = request.model_dump(mode="json")
    confirmation_hash = _canonical_hash(payload)
    reviewer_id = actor["id"]
    with uow_factory(patient_id=patient_id) as uow:
        draft = uow.get_draft(draft_id)
        if draft is None or draft.get("patient_id") != patient_id or draft.get("encounter_id") != encounter_id:
            raise ExtractionError("NOT_FOUND", 404, "Draft not found.")
        encounter = uow.get_encounter(encounter_id)
        if encounter is None or encounter.get("patient_id") != patient_id:
            raise ExtractionError("NOT_FOUND", 404, "Draft not found.")

        if draft.get("state") == "confirmed":
            if draft.get("version") == request.expected_version and draft.get("confirmation_hash") == confirmation_hash:
                return draft["confirmation_response"], True
            raise ExtractionError("CONFIRMATION_CONFLICT", 409, "Draft has already been confirmed with different content.")
        if draft.get("state") != "draft" or draft.get("version") != request.expected_version:
            raise ExtractionError("STALE_DRAFT", 409, "Draft version is no longer current.")

        timestamp = now()
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise RuntimeError("now must return an aware datetime")
        timestamp = timestamp.astimezone(timezone.utc)
        resource_id = str(uuid.uuid4())
        resource = {
            "id": resource_id,
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "category": request.approved_category,
            "summary": request.resource_summary,
            "reviewed_at": timestamp,
            "source_draft_id": draft_id,
        }
        uow.insert_resource(resource)
        audit_event = uow.append_audit({
            "occurred_at": timestamp, "actor_id": reviewer_id,
            "patient_id": patient_id, "action": "extraction.confirmed",
            "encounter_id": encounter_id, "purpose": None, "categories": [request.approved_category],
            "decision": "SUCCESS", "consent_id": None, "policy_version": None,
            "request_id": str(uuid.uuid4()),
        })
        audit_event_id = audit_event.get("id") if isinstance(audit_event, dict) else None
        if not isinstance(audit_event_id, str) or not audit_event_id:
            raise RuntimeError("audit append must return an event id")
        response = ConfirmationResponse(
            draft_id=draft_id, state="confirmed", resource_id=resource_id,
            category=request.approved_category, confirmed_at=timestamp,
            reviewer_id=reviewer_id, audit_event_id=audit_event_id,
        ).model_dump(mode="json")
        # Store the complete reviewed payload on the draft for admin-only review history.
        uow.confirm_draft(
            draft_id, confirmation_hash, response, payload, reviewer_id, timestamp,
        )
    return response, False
