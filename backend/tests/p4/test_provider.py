import pytest

from aarogyashield.extraction.ports import ProviderError
from aarogyashield.extraction.provider import FixtureProvider, GemmaProvider, validate_result


def test_fixture_is_explicit_and_validated():
    result = FixtureProvider().extract(b"bytes", "image/png", "req")
    assert result["source_mode"] == "fixture"
    assert result["proposed_json"]["document_type"] == "referral"


def test_identity_output_rejected():
    result = FixtureProvider().extract(b"bytes", "image/png", "req")["proposed_json"]
    result["patient_id"] = "p-secret"
    with pytest.raises(ProviderError):
        validate_result(result)


def test_invalid_json_no_provider_result():
    with pytest.raises(ProviderError):
        validate_result("not-json")


def test_gemma_requires_explicit_credentials_and_model():
    with pytest.raises(ValueError):
        GemmaProvider("", "gemma-4-26b-a4b-it")
