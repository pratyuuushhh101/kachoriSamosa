"""Opt-in smoke check for fixture mode or one live Gemma image request.

Live requests use only the generated synthetic referral fixture. This command
does not fall back between modes and never prints credentials or request headers.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .images import sanitize_image
from .provider import PROMPT_VERSION, FixtureProvider, GemmaProvider

DEFAULT_MODEL_ID = "gemma-4-26b-a4b-it"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_IMAGE = REPO_ROOT / "fixtures" / "referrals" / "synthetic-referral.png"
EVIDENCE_DIR = REPO_ROOT / "docs" / "ai" / "evidence"


def make_outbound_assertion(model_id: str, image_bytes: bytes, mime_type: str, result: dict[str, bool]):
    """Inspect the SDK's prepared HTTP request without retaining or logging it."""
    def assert_request(request: Any) -> None:
        path = urlsplit(str(request.url)).path
        result["model_id"] = f"/models/{model_id}:generateContent" in path
        try:
            payload = json.loads(request.content)
        except (ValueError, TypeError, AttributeError):
            result["image_bytes"] = False
            return

        def visit(value: Any) -> bool:
            if isinstance(value, dict):
                data = value.get("inlineData", value.get("inline_data"))
                if isinstance(data, dict):
                    encoded = data.get("data")
                    request_mime = data.get("mimeType", data.get("mime_type"))
                    if isinstance(encoded, str) and request_mime == mime_type:
                        try:
                            if base64.b64decode(encoded, validate=True) == image_bytes:
                                return True
                        except (ValueError, TypeError):
                            pass
                return any(visit(child) for child in value.values())
            if isinstance(value, list):
                return any(visit(child) for child in value)
            return False

        result["image_bytes"] = visit(payload)

    return assert_request


def _write_reviewed_evidence(*, model_id: str, sdk_version: str, mime_type: str,
                             image_hash: str, response: dict[str, Any], timestamp: datetime) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"live-smoke-{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
    record = {
        "status": "live_call_succeeded_and_human_reviewed",
        "checked_at_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "model_id": model_id,
        "sdk": "google-genai",
        "sdk_version": sdk_version,
        "prompt_version": PROMPT_VERSION,
        "image_mime_type": mime_type,
        "synthetic_image_sha256": image_hash,
        "outbound_model_assertion": True,
        "outbound_image_bytes_assertion": True,
        "source_mode": "live",
        "human_reviewed_response": response,
    }
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("fixture", "live"), required=True,
                        help="Choose exactly one mode; live never falls back to fixture.")
    args = parser.parse_args(argv)

    try:
        raw = DEFAULT_IMAGE.read_bytes()
    except OSError:
        print("status=ERROR reason=synthetic_image_unavailable")
        return 2
    try:
        clean, mime_type = sanitize_image(raw, "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg")
    except Exception:
        print("status=ERROR reason=invalid_smoke_image")
        return 2

    if args.mode == "fixture":
        result = FixtureProvider().extract(clean, mime_type, "p4-smoke-fixture")
        print(json.dumps({"status": "ok", **result}, ensure_ascii=False))
        return 0

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("status=BLOCKED reason=GEMINI_API_KEY_missing live_call_made=false")
        return 2
    model_id = os.environ.get("GEMMA_MODEL_ID", DEFAULT_MODEL_ID)
    if not model_id.startswith("gemma-"):
        print("status=ERROR reason=GEMMA_MODEL_ID_must_name_Gemma live_call_made=false")
        return 2

    observed = {"model_id": False, "image_bytes": False}
    observer = make_outbound_assertion(model_id, clean, mime_type, observed)
    try:
        provider = GemmaProvider(api_key, model_id, timeout_seconds=30, request_observer=observer)
        result = provider.extract(clean, mime_type, "p4-live-smoke")
        sdk_version = importlib.metadata.version("google-genai")
    except Exception as exc:
        print(f"status=ERROR reason=live_call_failed exception_type={type(exc).__name__} live_call_made=true")
        return 2
    if not observed["model_id"] or not observed["image_bytes"]:
        print("status=ERROR reason=outbound_request_assertion_failed live_call_made=true")
        return 3

    timestamp = datetime.now(timezone.utc)
    image_hash = hashlib.sha256(clean).hexdigest()
    print(json.dumps({
        "status": "live_call_succeeded_candidate_requires_human_review",
        "model_id": model_id,
        "sdk": "google-genai",
        "sdk_version": sdk_version,
        "prompt_version": result["prompt_version"],
        "image_mime_type": mime_type,
        "synthetic_image_sha256": image_hash,
        "outbound_model_assertion": observed["model_id"],
        "outbound_image_bytes_assertion": observed["image_bytes"],
        "source_mode": result["source_mode"],
        "candidate_response": result["proposed_json"],
    }, ensure_ascii=False))
    if sys.stdin.isatty() and input("Type REVIEWED to save this synthetic response as evidence: ").strip() == "REVIEWED":
        path = _write_reviewed_evidence(model_id=model_id, sdk_version=sdk_version,
                                        mime_type=mime_type, image_hash=image_hash,
                                        response=result["proposed_json"], timestamp=timestamp)
        print(f"evidence_saved={path.relative_to(REPO_ROOT)}")
    else:
        print("evidence_saved=false reason=human_review_not_confirmed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
