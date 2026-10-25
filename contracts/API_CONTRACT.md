# AarogyaShield — Frozen Cross-Branch Contract v1

Read with [the implementation plan](../WORK_IMPLEMENTATION.md). This is the agreed **target to implement**, not a report of existing endpoints. P1/P2/P4 own their wire DTOs and feature-local Protocols; P3 owns real storage adapters. Changing a path, field, status, enum, port or seeded ID requires the contract-change procedure in [the guardrails](../GUARDRAILS.md).

## 1. Common rules

- Base path `/api`; JSON uses snake_case; unknown request fields are rejected. IDs are opaque strings, not necessarily UUIDs.
- Roles: `patient`, `dentist`, `admin`. Categories: `dental`, `safety_summary`, `restricted`. Grantable categories: only the first two. Purpose: only `dental-consult`.
- Datetimes are aware ISO-8601 UTC strings with `Z`. Store/compare in UTC; UI displays `Asia/Kolkata`. Reject naive datetimes.
- Success bodies are direct objects; lists use `{ "items": [...] }`. Errors use `{ "code": "...", "message": "...", "request_id": "..." }`. No traceback, raw validation input, provider reply, hidden record IDs or clinical text in errors.
- Common statuses: 401 no valid session; 403 forbidden or no consent; 404 nonexistent/inaccessible object; 409 stale version/idempotency conflict; 422 invalid structured fields; 413 upload size; 415 unsupported media; 502 invalid provider response; 503 dependency unavailable. Malformed image bytes use 400. An error may include `Retry-After` metadata, never a chart body.
- All clinical, consent, draft, session and audit responses, including errors, use `Cache-Control: no-store`. Request IDs appear in `X-Request-ID`; chart payloads never go to application logs.
- Use same-origin browser/API in the assembled app. Development Vite proxies `/api`; no wildcard credentialed CORS. State-changing requests use `X-CSRF-Token` from the server session. Origin checks use the configured origin. Demo-session creation checks origin before a session/CSRF token exists.
- Session cookie: `aarogya_session`, HttpOnly, SameSite=Lax, Path=/, Secure on HTTPS; lifetime 2 hours. Local HTTP mode explicitly sets Secure=false. Signed cookie has session ID and expiry only; server session lookup establishes identity and role. Signing secret is server-only.
- No browser request may establish actor identity through `actor_id`, `role` or a free-form `patient_id`. Explicit patient IDs are accepted only for admin extraction and validated against seeded objects.

### Stable synthetic IDs and scenario

| Object | ID / properties |
| --- | --- |
| Patient A / B | `p-demo-1` / `p-demo-2` |
| Patient personas | `patient-a` → A; `patient-b` → B |
| Dentist personas | `dentist-a` → `d-demo-1`; `dentist-b` → `d-demo-2` |
| Admin persona | `admin-demo` → actor `a-demo-1` |
| Encounters | `E1` → A, assigned `d-demo-1`; `E2` → B, assigned `d-demo-2` |
| Notice | `N1`, version `notice-en-1`, English, body SHA-256 |
| A's resources | `R-dental` (`dental`); `R-safety` (`safety_summary`); `R-restricted` (`restricted`) |
| Restricted marker | `RESTRICTED_SENTINEL_DO_NOT_SHARE` appears only in synthetic restricted content/test fixtures |
| Initial state | No consent grants; all seeded chart resources reviewed; timestamps relative to seed clock |

Patients may see their own restricted content through the patient-self endpoint. The leak-marker prohibition applies to unauthorized/dentist responses, audit and logs, not the authorized patient's own chart.

## 2. HTTP endpoints

| Owner | Method / path | Permission / result |
| --- | --- | --- |
| P1 | `POST /api/demo/session` | Demo mode only; `{persona_id}`; sets cookie and returns `Session` |
| P1 | `GET /api/me` | Any session; returns `Session` |
| P1 | `POST /api/logout` | Session + CSRF; invalidates server session, expires cookie; 204 |
| P1 | `GET /api/patients/me/notice?encounter_id=E1` | Patient owns encounter; returns `NoticeView` |
| P1 | `GET /api/patients/me/chart?encounter_id=E1` | Patient owns encounter; returns `{encounter_id, resources}`; own view, not a dentist bypass |
| P2 | `POST /api/consents` | Patient + CSRF; grant request → `Grant`; first 201, exact retry 200 |
| P2 | `GET /api/consents` | Patient's own grant history → `{items: Grant[]}` |
| P2 | `POST /api/consents/{id}/withdraw` | Owner patient + CSRF; `{expected_version}` → `Grant`, 200 |
| P2 | `GET /api/encounters/{id}/chart?purpose=dental-consult` | Assigned dentist; `ChartResponse`, or safe error |
| P3 | `GET /api/audit/me?after_seq=0&limit=50` | Patient only; own metadata events in ascending seq; limit 1–100 |
| P3 | `POST /api/audit/verify` | Admin + CSRF; empty object → `VerificationResult` |
| P3 | `GET /api/health` | Public liveness → `{status:"ok"}`; separate internal DB readiness check |
| P4 | `POST /api/extraction-drafts` | Admin + CSRF; multipart `image`, `patient_id`, `encounter_id`; returns `Draft`, 201 |
| P4 | `POST /api/extraction-drafts/{id}/confirm` | Admin reviewer + CSRF; `ConfirmRequest` → `ConfirmationResponse`; first 201, exact retry 200 |

The dentist can use a known encounter ID from the fixed demo scenario; there is no unauthenticated patient-list or raw-resource endpoint. Patient notice/self chart requests for someone else's encounter return indistinguishable 404. Admin may review only valid seeded patient/encounter bindings. There is no public draft-list/get endpoint; the original draft response remains in the admin review page until logout/refresh. Re-upload is acceptable if the page is lost in this MVP.

### Session

```json
{
  "actor": {"id":"patient-a","role":"patient","patient_id":"p-demo-1","clinician_id":null,"display_name":"Synthetic Patient A"},
  "csrf_token":"server-generated-token",
  "expires_at":"2030-01-01T12:00:00Z",
  "demo_mode":true
}
```

Dates in examples are illustrative; runtime fixtures use a frozen or relative clock. Dentist actor has `patient_id=null`, `clinician_id="d-demo-1"`; admin has both null. A session's actor is resolved from a seeded user, not accepted from a JSON actor body. `patient-a` is both the patient persona ID and its actor ID; patient entity ID remains `p-demo-1`.

### NoticeView and self chart

`NoticeView = {id, version, language, body, sha256, encounter_id, recipient_id, purpose, selectable_categories, default_expires_at}`. Defaults: language `en`, selectable categories `["dental","safety_summary"]`, expiry now + 2 hours. No default consent selections. Notice max length 10,000 characters; hash exact UTF-8 bytes, no newline normalization after publication. Maximum grant lifetime 24 hours from grant time.

Self chart resources use `{id, category, summary, reviewed_at}`; summaries max 2,000 characters. The patient endpoint derives patient identity from the session and validates encounter ownership before querying content.

### Grant request and result

```json
{
  "recipient_id":"d-demo-1",
  "encounter_id":"E1",
  "purpose":"dental-consult",
  "categories":["dental","safety_summary"],
  "expires_at":"2030-01-01T12:00:00Z",
  "notice_id":"N1",
  "notice_version":"notice-en-1",
  "notice_hash":"64-lowercase-hex-characters-from-the-returned-notice",
  "confirmed":true,
  "idempotency_key":"browser-generated-random-key"
}
```

The example hash is a descriptive placeholder, not a valid test fixture hash. Real tests compute a 64-character digest. `idempotency_key` is 16–128 printable ASCII characters. Canonical request hashing sorts/deduplicates categories and includes all other semantic fields. Empty scopes, unknown categories and non-affirmative confirmation use 422; stale/mismatched notice version/hash uses 409.

`Grant = {id, version, patient_id, recipient_id, encounter_id, purpose, categories, notice_id, notice_version, notice_hash, starts_at, expires_at, status, withdrawn_at, is_current}`.

Status is `active`, `withdrawn` or computed `expired`. `version` is a monotonically increasing **grant generation** per `(patient_id, recipient_id, encounter_id, purpose)`, not a mutable row-update counter. A fresh grant produces a new row/version; withdrawal preserves that version and sets status/time. `starts_at` is server grant time. `is_current` is derived from the maximum version in that tuple.

**Supersession:** always select the highest version for the exact tuple, then evaluate its status/time/scope. Never union generations or fall back to an older grant after the latest was withdrawn/expired. Older rows are historical even if their stored status was active; UI labels them historical using `is_current=false`. A later deliberate grant may restore sharing with a new version.

**Retry behavior:** an exact idempotency retry returns the stored original creation response and no new event, even if that grant was later withdrawn. This historical response does not represent current permission: the UI refreshes `GET /api/consents` after grant submission. A reused key with a different canonical payload is 409. Retry never reactivates a row.

Withdrawal first verifies ownership and supplied generation. Matching version + active → withdrawn; matching version + already withdrawn → existing result, one event total; wrong version → 409. A historical, non-current grant cannot be withdrawn to alter current sharing and returns 409. Expired current grant returns 409. No broad “withdraw every grant” behavior is implicit.

### ChartResponse and denials

```json
{
  "encounter_id":"E1",
  "consent_id":"C1",
  "decision":"ALLOW_REDACTED",
  "resources":[
    {"id":"R-dental","category":"dental","summary":"Synthetic referral: tooth pain"},
    {"id":"R-safety","category":"safety_summary","summary":"Synthetic curated summary: penicillin allergy"}
  ],
  "withheld_categories":["restricted"],
  "reason":"Only categories in the current sharing grant are returned.",
  "policy_version":"dental-policy-1",
  "audit_event_id":"A1"
}
```

Successful decisions are `ALLOW` or `ALLOW_REDACTED`; denial is a 403 error with code `NO_ACTIVE_CONSENT` (or `PURPOSE_NOT_ALLOWED`) and no `resources`. A wrong-role request is 403 `ROLE_NOT_ALLOWED`; wrong/unassigned encounter is 404 `NOT_FOUND`.

For this fixed scenario, withheld labels come from the known policy universe `{dental,safety_summary,restricted}` minus granted readable categories; sorted, constant policy labels reveal no hidden record ID/count. `restricted` is always withheld from dentists. The response is `ALLOW_REDACTED` whenever any policy category is withheld, even if there is no corresponding stored row. Include only reviewed resource rows in allowed categories, with exact fields `id,category,summary`; never draft evidence or source text. Empty permitted categories deny; no rows in a valid category is a successful empty result.

Evaluate `starts_at <= now < expires_at`, exact tuple, current generation, active state, valid known category set. Authorize first; only then query payloads with permitted categories. No grant, malformed grant, DB/audit failure or unknown purpose returns clinical content.

### Extraction shapes

Limits: image bytes ≤ 5 MiB, complete multipart request ≤ 6 MiB, decoded area ≤ 16,000,000 pixels, one PNG/JPEG, no EXIF in sanitized output. Provider timeout 30 seconds, at most 2 in-flight calls per single API worker, admission limit 5 extraction starts per session per minute (429 when exceeded). No automatic application retries. Use one API worker for this MVP's in-memory admission limiter; document that it is not a distributed limiter.

`ProposedExtraction` fields, all required and with extra fields forbidden:

```json
{
  "document_type":"referral",
  "encounter_hint":"dental referral",
  "dental_summary":"Synthetic referral for tooth pain",
  "medication_mentions":[],
  "allergy_mentions":["penicillin"],
  "sensitive_mentions":[],
  "uncertain_fields":[],
  "evidence_spans":[{"field":"allergy_mentions","text":"penicillin allergy"}]
}
```

Each string ≤ 2,000 chars; each array ≤ 20 entries; evidence text ≤ 300 chars per entry; total validated proposed JSON ≤ 32 KiB UTF-8. `uncertain_fields` entries must name schema fields. `document_type` must be `referral`. No patient/actor/consent identifiers may be output fields. Any unexpected identity-like value is flagged for manual rejection; model-extracted identity never binds storage.

`Draft = {id, version, patient_id, encounter_id, state, image_sha256, model_id, prompt_version, source_mode, proposed_json, warnings, suggested_category, created_at}`. Initial state `draft`, version 1, `suggested_category="restricted"`; source mode `live` or `fixture`. Patient/encounter are server-bound from the upload form, never model-generated. No stored public image URL. The raw/sanitized upload is removed from temporary storage after provider completion/failure; keep only its hash. Store structured drafts until explicit demo reset; disclose this retention.

`ConfirmRequest = {expected_version, corrected_json: ProposedExtraction, resource_summary, approved_category, human_reviewed, category_reviewed}`. Summary max 2,000 chars. Approved category must be one of the three categories; no preselected shareable category. `human_reviewed=true` is required. `category_reviewed=true` and empty `corrected_json.uncertain_fields` are required for `dental` or `safety_summary`. Otherwise return 422 and require the reviewer to choose `restricted` or resolve uncertainty.

`ConfirmationResponse = {draft_id, state:"confirmed", resource_id, category, confirmed_at, reviewer_id, audit_event_id}`. The version remains the original draft generation; do not increment it on confirmation. Store confirmation payload hash/response; same version+hash retry returns original result, changed retry returns 409. One resource per `source_draft_id` enforced by DB uniqueness. Only `resource_summary` and category enter the published content; evidence/sensitive mentions stay admin-only on the draft. This is reviewed synthetic data, not clinical advice.

## 3. Python ports and transaction contract

Use synchronous repository/unit-of-work interfaces. Provider I/O is bounded and outside the transaction. Feature-local test doubles return detached plain dictionaries; no SQLAlchemy class leaks across a feature boundary. Define narrow `TypedDict`/`Protocol` types locally to match the shapes above. These declarations may repeat only their feature's consumed subset; frozen semantics live here.

Every router exposes `create_router(ports) -> fastapi.APIRouter` with full `/api/...` paths. Its injected ports contain:

| Port | Shape / semantics | Provided at final wiring by |
| --- | --- | --- |
| `uow_factory` | Callable `(*, patient_id: str \| None = None)` → context manager | P3 |
| `now` | `() -> datetime`, aware UTC, fixed clock in tests | P3 |
| `current_actor` | FastAPI dependency callable → actor dict; validates signed session and server lookup | P1 `build_current_actor(ports)` |
| `require_csrf` | FastAPI dependency callable; session CSRF + Origin validation for mutations | P1 `build_require_csrf(ports)` |
| `settings` | Read-only settings object/config fields needed by feature | P3; documented names below |
| `provider` | `.extract(image_bytes: bytes, mime_type: str, request_id: str) -> ExtractionResult` | P4, extraction only |

P1 identity can bootstrap its router/dependency builders with `uow_factory`, `now`, `settings`; it does not require another feature's actor dependency to build its own. Both dependency builders live in `identity.sessions`. P2/P3 audit/P4 routers use injected dependency callables via FastAPI `Depends`. Each owns its small error type; P3 maps them into the shared error envelope at integration. Local harnesses install the same mapper behavior for their tests.

`ExtractionResult = {model_id, prompt_version, source_mode, proposed_json, warnings}`. Provider failure raises a feature-owned safe exception; it never returns a pretend successful result.

### Unit-of-work methods

All row dictionaries carry the fields above plus persistence metadata listed here. Missing row returns `None`, list query returns an empty list. Mutation methods stage changes in the existing transaction and return detached stored values; they do not commit. Services create UUID-like opaque IDs via standard UUID helpers except stable seed IDs.

| Method | Return / behavior |
| --- | --- |
| `get_user(persona_id)` | `{id,role,patient_id,clinician_id,display_name}` or None |
| `get_session(session_id)` | Session row including actor reference, CSRF token, expiry, revoked flag |
| `insert_session(row)` / `revoke_session(session_id)` | Store or invalidate session |
| `get_patient(patient_id)` | Synthetic patient metadata or None |
| `get_encounter(encounter_id)` | `{id,patient_id,recipient_id,type,status}` or None; no clinical text |
| `get_notice(notice_id)` / `get_published_notice(encounter_id)` | Notice row plus published flag and scope metadata |
| `list_resources(patient_id, encounter_id, categories)` | Reviewed resource rows only, filtered in DB by explicit category set; P1 passes all three only after self authorization |
| `list_grants(patient_id, encounter_id=None)` | Grant rows; service computes effective expiry/current flags |
| `get_grant(grant_id)` / `insert_grant(row)` | Grant lookup/stage insert |
| `withdraw_grant(grant_id, withdrawn_at)` | Update lifecycle state only; scope/version immutable |
| `get_idempotency(patient_id, endpoint, key)` | `{request_hash,response_json}` or None |
| `insert_idempotency(patient_id, endpoint, key, request_hash, response_json)` | Unique patient+endpoint+key, staged with grant |
| `get_draft(draft_id)` / `insert_draft(row)` | Draft row; includes admin creator/review metadata |
| `confirm_draft(draft_id, confirmation_hash, response_json, corrected_json, reviewer_id, confirmed_at)` | Set confirmed state and store retry/review fields |
| `insert_resource(row)` | Row includes patient/encounter/category, summary, reviewed_at, source_draft_id |
| `append_audit(event)` | Reserved sequence/hash event; same transaction, delegates to P3 audit service |
| `list_audit(patient_id, after_seq, limit)` | Patient-filtered minimal events |
| `get_audit_snapshot()` | `(all_events_in_seq_order, head)` from one consistent snapshot, admin verifier only |

Storage data for `get_draft` also includes confirmation hash/response and reviewer/time after confirmation. Inserted resources store `summary` in controlled content JSON internally; exposed row projection has only declared resource fields. P4 populates `reviewed_at` from its server clock at explicit confirmation. Grant rows include `notice_version` and `notice_hash` snapshots. Additional ORM plumbing remains private to P3.

For an owned business operation, enter `with uow_factory(patient_id=patient_id) as uow`. PostgreSQL locks that patient row first, then rereads current state before checking permission. Audit append locks one shared audit-head row second and holds it until commit. Every relevant grant, withdraw, chart read and draft confirmation uses this order. `patient_id=None` is for session operations, safe metadata resolution, admin verification and health; it cannot be used for clinical authorization/mutation without acquiring a patient-scoped transaction afterwards.

Patient unknown until grant/draft lookup: use a **metadata-only repository lookup**, obtain patient ID, then enter the patient-locked transaction and repeat lookup/authorization. Implement `get_grant`/`get_draft` metadata projection in the platform adapter when called without patient scope: only ID, patient ID, encounter ID and owner/reference IDs; no content, proposed JSON or stored response. Full row lookup is permitted only in the patient-scoped transaction after role/binding checks. No HTTP response returns this preliminary lookup.

A successful context exits by committing; exceptions roll back. Chart allow/deny event must commit before a response is sent; a dependency failure makes the response 503 without chart. Inaccessible encounter lookup may append a safe denial with `patient_id=null` and no guessed hidden identifiers. Internal role/session rejection can be operational metadata without a clinical audit row. Avoid writes during streaming responses.

## 4. Audit format and canonical hash

Allowed event fields before hashes:

```json
{
  "id":"A1",
  "seq":1,
  "occurred_at":"2030-01-01T10:00:00.000000Z",
  "actor_id":"patient-a",
  "patient_id":"p-demo-1",
  "action":"consent.granted",
  "encounter_id":"E1",
  "purpose":"dental-consult",
  "categories":["dental","safety_summary"],
  "decision":"SUCCESS",
  "consent_id":"C1",
  "policy_version":"dental-policy-1",
  "request_id":"req-1"
}
```

All keys are present on the stored event; inapplicable metadata is null and categories is an empty list. Callers pass `occurred_at` from the injected clock and the remaining metadata, excluding `id` and `seq`; the append service assigns those two fields under the audit-head lock. Allowed actions: `consent.granted`, `consent.withdrawn`, `chart.allowed`, `chart.denied`, `extraction.drafted`, `extraction.failed`, `extraction.confirmed`. Decisions: `SUCCESS`, `ALLOW`, `ALLOW_REDACTED`, `DENY`, `ERROR`. No arbitrary free-text payload extension. Arrays of categories are sorted; timestamp precision is six decimal digits UTC. Resource IDs, notices' full bodies, clinical/draft text, source image, model prompts and credentials are absent.

The append service adds `previous_hash` and `event_hash`. Genesis previous hash is 64 zeroes; first sequence 1. Compute:

```python
canonical = json.dumps(event_without_hashes, sort_keys=True,
                       separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False).encode("utf-8")
event_hash = hashlib.sha256(canonical + previous_hash.encode("ascii")).hexdigest()
```

The head row stores `{chain_id, last_seq, last_hash}` and changes atomically with append. Reset creates a new chain ID. Verifier compares the chain with that head and returns `{valid, checked_count, first_invalid_seq, reason, chain_id, head_hash}`; invalid seq/reason are null on success. Patient timeline projects metadata fields without hashes/other patients; admin verifier sees aggregate result. A copied chain plus original head detects tail deletion; rewriting chain **and head** defeats this demonstration. Never label it immutable or certified evidence.

## 5. Settings and environment

P3 exposes validated settings with these names; secret values never enter frontend bundles:

| Environment | Settings attribute | Meaning |
| --- | --- | --- |
| `DATABASE_URL` | `database_url` | Private PostgreSQL DSN |
| `DEMO_MODE` | `demo_mode` | Explicit demo persona/seed/reset enablement |
| `SESSION_SECRET` | `session_secret` | Required signing secret; reject placeholder outside tests |
| `COOKIE_SECURE` | `cookie_secure` | true for public HTTPS; false only for local HTTP |
| `APP_ORIGIN` | `app_origin` | Exact browser origin for Origin/CSRF checks |
| `AI_MODE` | `ai_mode` | `live` or explicit `fixture`; no automatic fallback |
| `GEMINI_API_KEY` | `gemini_api_key` | Backend-only; required in live mode |
| `GEMMA_MODEL_ID` | `gemma_model_id` | Actual account-supported Gemma ID, verified by P4 |
| `UPLOAD_MAX_BYTES` | `upload_max_bytes` | Default 5,242,880; bounded by documented multipart cap |
| `AI_TIMEOUT_SECONDS` | `ai_timeout_seconds` | Default 30 |

Frontend: `VITE_API_MODE=real|mock`, API path `/api`. Only P1 owns frontend env handling. Integration rejects mock mode for the production demo build. P4 provider uses prompt version `referral-extract-1` until a documented reviewed change.
