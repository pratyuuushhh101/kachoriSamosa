from __future__ import annotations

from typing import Any, Protocol

from .schemas import ProposedExtraction


class ProviderError(Exception):
    """Safe provider failure. Never include source or model text in the message."""


class InvalidProviderResponse(ProviderError):
    """The provider answered, but its reply did not match the extraction contract."""


class ExtractionProvider(Protocol):
    def extract(self, image_bytes: bytes, mime_type: str, request_id: str) -> dict[str, Any]: ...


class UnitOfWork(Protocol):
    def get_patient(self, patient_id: str) -> dict[str, Any] | None: ...
    def get_encounter(self, encounter_id: str) -> dict[str, Any] | None: ...
    def insert_draft(self, row: dict[str, Any]) -> dict[str, Any]: ...
    def get_draft(self, draft_id: str) -> dict[str, Any] | None: ...
    def confirm_draft(self, draft_id: str, confirmation_hash: str, response_json: dict[str, Any],
                      corrected_json: dict[str, Any], reviewer_id: str, confirmed_at: Any) -> dict[str, Any]: ...
    def insert_resource(self, row: dict[str, Any]) -> dict[str, Any]: ...
    def append_audit(self, event: dict[str, Any]) -> dict[str, Any]: ...


class Ports(Protocol):
    provider: ExtractionProvider
    current_actor: Any
    require_csrf: Any
    now: Any
    uow_factory: Any
    image_max_bytes: int
    ai_mode: str
