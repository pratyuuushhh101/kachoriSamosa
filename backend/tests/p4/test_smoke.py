import base64
import json
from types import SimpleNamespace

from aarogyashield.extraction.smoke import main, make_outbound_assertion


def test_fixture_smoke_is_visibly_fixture(capsys):
    assert main(["--mode", "fixture"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["source_mode"] == "fixture"
    assert "no live model call" in output["warnings"][0]


def test_live_smoke_without_key_stops_without_fallback(monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert main(["--mode", "live"]) == 2
    output = capsys.readouterr().out
    assert "BLOCKED" in output and "live_call_made=false" in output
    assert "source_mode" not in output


def test_outbound_assertion_checks_model_and_exact_image_bytes():
    image = b"sanitized-synthetic-png"
    body = {"contents": [{"parts": [{"inlineData": {
        "mimeType": "image/png", "data": base64.b64encode(image).decode("ascii"),
    }}]}]}
    request = SimpleNamespace(
        url="https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent?key=secret",
        content=json.dumps(body).encode(),
    )
    observed = {"model_id": False, "image_bytes": False}
    make_outbound_assertion("gemma-4-26b-a4b-it", image, "image/png", observed)(request)
    assert observed == {"model_id": True, "image_bytes": True}


def test_outbound_assertion_detects_wrong_model_or_image():
    observed = {"model_id": False, "image_bytes": False}
    request = SimpleNamespace(url="https://example.test/v1beta/models/gemma-other:generateContent",
                              content=json.dumps({"contents": [{"parts": [{"text": "not an image"}]}]}).encode())
    make_outbound_assertion("gemma-4-26b-a4b-it", b"image", "image/png", observed)(request)
    assert observed == {"model_id": False, "image_bytes": False}
