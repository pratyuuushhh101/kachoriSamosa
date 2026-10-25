from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Form, Request, Response, UploadFile
from fastapi.responses import JSONResponse

from .images import ImageInputError
from .confirmation import confirm_draft
from .schemas import ConfirmRequest, ConfirmationResponse, DraftResponse
from .service import ExtractionError, create_draft

MAX_REQUEST_BYTES = 6 * 1024 * 1024


class AdmissionLimiter:
    """Per-worker in-memory admission limit; use one API worker for this MVP."""
    def __init__(self, limit: int = 5, window_seconds: int = 60):
        self.limit, self.window_seconds = limit, window_seconds
        self._lock = threading.Lock()
        self._starts: dict[str, deque[float]] = defaultdict(deque)

    def admit(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._starts[key]
            while bucket and now - bucket[0] >= self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True


def create_router(ports: Any) -> APIRouter:
    router = APIRouter()
    limiter = AdmissionLimiter()

    @router.post("/api/extraction-drafts", status_code=201, response_model=DraftResponse)
    async def upload_draft(
        request: Request,
        image: UploadFile = File(...),
        patient_id: str = Form(...),
        encounter_id: str = Form(...),
        actor: dict[str, Any] = Depends(ports.current_actor),
        _csrf: Any = Depends(ports.require_csrf),
        response: Response = None,
    ) -> Any:
        if response is not None:
            response.headers["Cache-Control"] = "no-store"
        if actor.get("role") != "admin":
            return JSONResponse(status_code=403, headers={"Cache-Control": "no-store"}, content={"code": "ROLE_NOT_ALLOWED", "message": "Administrator role required."})
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_REQUEST_BYTES:
                    return JSONResponse(status_code=413, headers={"Cache-Control": "no-store"}, content={"code": "UPLOAD_TOO_LARGE", "message": "Upload exceeds the request limit."})
            except ValueError:
                return JSONResponse(status_code=400, headers={"Cache-Control": "no-store"}, content={"code": "INVALID_REQUEST", "message": "Invalid request."})
        session_id = str(actor.get("session_id") or actor.get("id") or "")
        if not patient_id or len(patient_id) > 100 or not encounter_id or len(encounter_id) > 100:
            return JSONResponse(status_code=422, headers={"Cache-Control": "no-store"}, content={"code": "INVALID_REQUEST", "message": "Invalid patient or encounter selection."})
        if not limiter.admit(session_id):
            return JSONResponse(status_code=429, headers={"Cache-Control": "no-store", "Retry-After": "60"}, content={"code": "RATE_LIMITED", "message": "Too many extraction requests."})
        try:
            raw = await image.read(5 * 1024 * 1024 + 1)
            if len(raw) > 5 * 1024 * 1024:
                raise ImageInputError("UPLOAD_TOO_LARGE", 413)
            row = create_draft(actor=actor, patient_id=patient_id, encounter_id=encounter_id,
                               image_bytes=raw, mime_type=image.content_type or "", ports=ports)
            return {key: row[key] for key in DraftResponse.model_fields}
        except ImageInputError as exc:
            return JSONResponse(status_code=exc.status, headers={"Cache-Control": "no-store"}, content={"code": exc.code, "message": "Invalid image upload."})
        except ExtractionError as exc:
            return JSONResponse(status_code=exc.status, headers={"Cache-Control": "no-store"}, content={"code": exc.code, "message": exc.message})
        finally:
            await image.close()

    @router.post("/api/extraction-drafts/{draft_id}/confirm", status_code=201, response_model=ConfirmationResponse)
    async def confirm_draft_route(
        draft_id: str,
        body: ConfirmRequest = Body(...),
        actor: dict[str, Any] = Depends(ports.current_actor),
        _csrf: Any = Depends(ports.require_csrf),
        response: Response = None,
    ) -> Any:
        if response is not None:
            response.headers["Cache-Control"] = "no-store"
        try:
            result, retried = confirm_draft(
                actor=actor, draft_id=draft_id, request=body,
                uow_factory=ports.uow_factory, now=ports.now,
            )
            if retried and response is not None:
                response.status_code = 200
            return result
        except ExtractionError as exc:
            return JSONResponse(status_code=exc.status, headers={"Cache-Control": "no-store"}, content={"code": exc.code, "message": exc.message})

    return router
