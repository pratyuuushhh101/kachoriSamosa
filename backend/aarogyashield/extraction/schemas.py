from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    text: str = Field(max_length=300)


class ProposedExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_type: Literal["referral"]
    encounter_hint: str = Field(max_length=2000)
    dental_summary: str = Field(max_length=2000)
    medication_mentions: list[str] = Field(max_length=20)
    allergy_mentions: list[str] = Field(max_length=20)
    sensitive_mentions: list[str] = Field(max_length=20)
    uncertain_fields: list[str] = Field(max_length=20)
    evidence_spans: list[EvidenceSpan] = Field(max_length=20)

    @field_validator("medication_mentions", "allergy_mentions", "sensitive_mentions", "uncertain_fields")
    @classmethod
    def validate_entries(cls, values: list[str]) -> list[str]:
        if any(len(value) > 2000 for value in values):
            raise ValueError("entry too long")
        return values

    @field_validator("uncertain_fields")
    @classmethod
    def known_uncertain_fields(cls, values: list[str]) -> list[str]:
        allowed = set(cls.model_fields)
        if any(value not in allowed for value in values):
            raise ValueError("unknown uncertain field")
        return values


class DraftResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    version: int
    patient_id: str
    encounter_id: str
    state: Literal["draft"]
    image_sha256: str
    model_id: str
    prompt_version: str
    source_mode: Literal["live", "fixture"]
    proposed_json: ProposedExtraction
    warnings: list[str]
    suggested_category: Literal["restricted"]
    created_at: datetime
