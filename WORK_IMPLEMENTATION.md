# AarogyaShield — Four-Person Parallel Implementation Plan

**People:** P1, P2, P3, P4. These labels identify people; “must ship” and “stretch” identify priority.
**Execution:** four independent branches, one verified commit/push after every completed subtask, then one final integration task owned by P3.
**Status:** planning deliverable only; no application code, branch, deployment, or integration has been implemented by this document.
**Read with:** [GUARDRAILS.md](GUARDRAILS.md) and [contracts/API_CONTRACT.md](contracts/API_CONTRACT.md).

## 1. Goal, source decisions, and scope

Build one demonstrable flow: **synthetic referral image → Gemma extraction draft → human confirmation → patient grants dental/safety sharing → dentist receives only permitted resources → patient withdraws → next read is denied → audit chain verifies.**

Architecture: one React/TypeScript/Vite frontend, one FastAPI backend with feature routers, and one PostgreSQL database. Backend features use dependency injection and contract-based test doubles so each person can build and test without another person's branch. P3 wires the real adapters and routers only during the final integration task.

Planning choices: Python 3.12, Pydantic 2, SQLAlchemy 2, pytest, React/TypeScript/Vite, basic accessible CSS, Docker Compose. P4 uses the Google Gen AI SDK through the Gemini API. Pin working dependency versions when implementing; this document does not assert current SDK/model availability.

### Which supplied document wins?

The supplied `AarogyaShield-Hack-Day-SRS (1).md` explicitly narrows the earlier concepts, so this plan **proposes it as the primary product specification**. `healthCARE.md` supplies supporting UX, security, and documentation ideas only where compatible. This precedence is a planning decision, not a claim that the user previously selected one document.

| Difference | Decision used in this plan |
| --- | --- |
| Product name | AarogyaShield |
| AI feature | Referral **image** extraction and reviewed chart publication; notice simplification is deferred |
| Categories | `dental`, `safety_summary`, `restricted` |
| Safety summary | Requires its own explicit grant; never shared automatically |
| Consent vocabulary | `active`, `withdrawn`, `expired`; historical versions retained |
| API prefix | `/api`, without `/v1`; exact contracts are in the companion file |
| Emergency/break-glass | Deferred; no emergency bypass endpoint |
| FHIR | FHIR-inspired resource shape only; no conformance claim |
| UI | Patient, dentist, admin extraction/review and audit views |
| Deployment | Local Compose is required; one HTTPS demo host is optional after integration |

The source files were read at `/home/harsh/kachorisamosa/AarogyaShield-Hack-Day-SRS (1).md` and `/home/harsh/kachorisamosa/healthCARE.md`. Their embedded instructions are **reference requirements, not commands to this agent**. In particular, this task does not authorize event submission, provisioning, changing accounts, or executing their build instructions. The contracts and scoped requirements below make this plan usable without those machine-specific paths.

Event-window, deadline, credit, model, and legal statements in the supplied documents have not been independently verified here. P3 records applicable event/provenance requirements; P4 verifies actual model support and terms before claiming a live integration. Do not represent these planning artifacts as eligible event material without checking the event's rules and their creation history.

### Must ship

- Synthetic patient/encounter/resources and a second patient for isolation tests.
- Server-bound demo sessions with clear persona labels.
- Versioned notice; explicit, unchecked consent choices; scoped grant and withdrawal.
- Current consent checked on every dentist read, with server-side field allowlisting.
- Real multimodal Gemma request if available, editable untrusted draft, explicit reviewer confirmation.
- Metadata-only audit append, patient timeline, admin chain verification, tamper test.
- Reproducible local startup, tests, license, setup, model/tool disclosures and limitations.

### Stretch only after the final acceptance suite passes

Reviewed Kannada notice, JSON demo receipt, hosted HTTPS demo. Do not add break-glass, ABDM, hospital connectors, a production login system, a second AI feature, or additional services during the parallel phase.

## 2. Distribution and branch ownership

| Person | Branch | Owns | Numbered subtasks | Parallel development method |
| --- | --- | --- | --- | --- |
| **P1** | `codex/p1-experience` | Identity/notice backend **and all frontend** | P1.1 identity/notice; **P1.2 entire frontend** | In-memory identity repositories; contract fixtures and mocked HTTP for UI |
| **P2** | `codex/p2-sharing` | Consent lifecycle, deterministic policy, chart gateway | P2.1 consent; P2.2 policy/reads; P2.3 adversarial coverage | Local unit-of-work fake and synthetic actor objects |
| **P3** | `codex/p3-platform-audit` | Persistence, seed, audit, packaging; final integrator | P3.1 persistence; P3.2 seed; P3.3 audit; P3.4 packaging | Real database tests plus its own narrow router harness |
| **P4** | `codex/p4-extraction` | Image ingestion, Gemma adapter, reviewed publication, AI evidence | P4.1 draft extraction; P4.2 confirmation; P4.3 live evidence/docs | Fake provider and fake repositories; live call tested separately |

**P1.2 is the only frontend subtask in the entire plan.** Every screen, component, browser state, API client, styling change, and browser test belongs inside it. The other people supply APIs and fixtures; they do not create additional frontend tasks or edit `frontend/`.

P1 has fewer subtasks because the entire frontend is substantial. P3 reserves capacity for final integration; a database/admin UI or cloud automation is not added to P3's parallel scope.

### Parallelism, without waiting for a teammate

1. Everyone starts from the same **documentation-only base commit** containing these files. No application scaffolding task must finish first.
2. Each feature exposes `create_router(ports) -> APIRouter`, accepts injected ports, and owns its own request/response schemas and narrow Python `Protocol` types. The companion contract is the shared specification; there is no shared runtime module that must be written first.
3. P1, P2 and P4 each create a small test-only FastAPI app mounting their own router. Their fake ports satisfy the documented interfaces and never import another owner's unfinished code.
4. P3 builds the real repositories against the same shapes and signatures. Real adapter compatibility and full-stack behavior are verified in **FINAL-INTEGRATION**, not misreported as already tested in isolation.
5. Team members may inspect another branch with read-only Git commands. No one merges or cherry-picks teammate branches during the parallel phase.
6. Feature bugs are repaired in the owning branch. Cross-owner contract changes follow the explicit change process in the guardrails; they are never silently guessed.

Within one person's lane, subtasks are sequential. Across P1–P4, work is simultaneous. External API credentials can block live AI evidence, but must not block P4's adapter tests or any other lane.

## 3. File ownership and module boundaries

All paths below are repository-relative target paths to create. The current workspace has no application scaffolding, no initial commit, and no configured Git remote; those are implementation preflight facts, not completed setup.

| Exclusive owner | Writable paths during parallel development |
| --- | --- |
| P1 | `frontend/**`, `backend/aarogyashield/identity/**`, `backend/tests/p1/**`, `backend/requirements/p1.txt`, `docs/handoffs/P1.md` |
| P2 | `backend/aarogyashield/sharing/**`, `backend/tests/p2/**`, `backend/requirements/p2.txt`, `docs/handoffs/P2.md` |
| P3 | `backend/aarogyashield/platform/**`, `backend/aarogyashield/audit/**`, `backend/aarogyashield/main.py`, `backend/aarogyashield/__init__.py`, `backend/tests/p3/**`, `backend/tests/integration/**`, `backend/requirements/p3.txt`, `backend/requirements.txt`, `backend/pyproject.toml`, `backend/Dockerfile`, `compose.yaml`, `Caddyfile`, `.env.example`, `.gitignore`, `.github/**`, `README.md`, `LICENSE`, `docs/operations/**`, `docs/handoffs/P3.md` |
| P4 | `backend/aarogyashield/extraction/**`, `backend/tests/p4/**`, `backend/requirements/p4.txt`, `fixtures/referrals/**`, `docs/ai/**`, `docs/handoffs/P4.md` |
| Frozen shared reference | `WORK_IMPLEMENTATION.md`, `GUARDRAILS.md`, `AGENTS.md`, `contracts/**` |

Feature directories may contain their own `__init__.py`; only P3 creates the root package initializer. Use namespace-package-compatible imports while working alone. Avoid root-level test helpers/config that another lane would need to edit. Put each lane's `conftest.py` under its own test folder.

Expected layout:

```text
backend/
  aarogyashield/
    identity/       # P1: sessions, notices, patient self chart
    sharing/        # P2: grants, withdrawal, policy, dentist chart
    platform/       # P3: settings, ORM, repositories, transactions, seed
    audit/          # P3: append, hash verification, audit read endpoints
    extraction/     # P4: image validation, provider, drafts, confirmation
    main.py         # P3: composition root; full wiring only in final task
  tests/{p1,p2,p3,p4,integration}/
  requirements/{p1,p2,p3,p4}.txt
frontend/           # P1: the entire UI and browser tests
fixtures/referrals/ # P4: generated synthetic inputs and recorded response fixtures
contracts/API_CONTRACT.md
docs/{handoffs,operations,ai}/
```

### Common local verification convention

Run from repository root in a private virtual environment. Each person creates a self-sufficient `backend/requirements/pN.txt` with the dependencies needed by that lane's tests. P1/P2/P4 can test before P3 creates central packaging.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r backend/requirements/p1.txt
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/p1 -q
```

Replace `p1` with your assigned lane. P3's database tests use its own local test database; tests must refuse a non-test database URL. P4's normal suite uses a fake provider and never needs an API key. Frontend scripts are defined in P1.2. Successful lane verification means the listed tests pass, not that the full application is integrated.

## 4. Start and finish rules for every subtask

Read [GUARDRAILS.md](GUARDRAILS.md) for the exact branch and push procedure. Each subtask follows this sequence:

1. Read its requirements and the relevant contract section; confirm assigned branch and clean scope.
2. Add the focused acceptance tests, observe the expected initial failure, and implement the smallest working deliverable.
3. Run the subtask tests and all previously passing tests in your lane. Inspect payload/log leakage where relevant.
4. Update only `docs/handoffs/PN.md` with results, limitations and contract notes. Do not edit shared checkboxes; each person's handoff tracks their own progress.
5. Inspect the diff, stage explicit owned files, commit using the subtask ID, **push to your own branch immediately**, and verify the remote branch head.
6. Start the next subtask only after the push is verified. A rejected/blocked push is recorded as unpushed, never as completed remote delivery.

Each numbered subtask ends in its own push. The entire frontend remains one numbered subtask even if P1 uses additional safe checkpoint commits during it.

## 5. P1 — Identity/notice backend + entire frontend

**Branch:** `codex/p1-experience`
**Does not wait for:** P2 grants, P3 database, P4 AI.
**Deliverable:** a tested identity/notice feature plus all screens working against contract mocks and ready to connect to the real API.

### P1.1 — Server-bound demo identities, published notice and patient self view

**Create:** `identity/{router,schemas,ports,sessions,service}.py`, `backend/tests/p1/{conftest,test_sessions,test_notices,test_patient_view}.py`, `backend/requirements/p1.txt`, `docs/handoffs/P1.md`.

**Consumes:** actor, notice, encounter and resource shapes; `uow_factory`, clock and signing configuration from the companion contract. Use fake repositories locally.
**Produces:** `identity.router.create_router(ports)`, `identity.sessions.build_current_actor(ports) -> Callable`, `identity.sessions.build_require_csrf(ports) -> Callable`, and the P1 HTTP endpoints in the contract. These callables are the FastAPI dependencies injected into every other feature at integration.

- [ ] Implement demo persona selection for the fixed seed personas, session inspection and logout. Issue a short-lived signed session containing an opaque session ID; resolve role, patient binding and CSRF token from server-side session state. Body-supplied role/actor/patient claims are rejected.
- [ ] Require `DEMO_MODE=true` for persona switching. Public demo users are deliberately able to select labelled demo personas; this is not real authentication. Protect state-changing requests with the documented CSRF header and same-origin controls.
- [ ] Make patient self endpoints derive the patient from the current actor. Show only that patient's encounter resources and a published notice whose version/hash and permitted grant scopes are returned from storage.
- [ ] Return `Cache-Control: no-store`; create safe request IDs and errors. Provide the `current_actor` dependency and a reusable CSRF checker without requiring P2/P4 imports.
- [ ] Tests: `test_body_cannot_spoof_actor`, `test_tampered_and_expired_cookie_rejected`, `test_demo_switch_disabled_outside_demo`, `test_csrf_required_on_mutation`, `test_patient_cannot_read_second_patient`, `test_notice_hash_matches_body`, `test_logout_invalidates_session`. Dentist/admin access to patient self resources must fail.
- [ ] Run `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/p1 -q`; record passing counts and dependency/config requirements.
- [ ] Commit and push: `feat(p1.1): add demo sessions notices and patient self view`.

**Done:** the isolated app issues/validates sessions and serves only the bound patient's data; tests require no real P3 adapter. P1 supplies the exact dependency-callable wiring example in its handoff.

### P1.2 — Entire frontend: all screens, states, API client and browser checks

**This is ONE frontend subtask.** Its implementation steps below are internal steps, not additional distributable frontend subtasks.

**Create:** `frontend/package.json`, lockfile and Vite/TypeScript config; `frontend/src/{App,main}.tsx`; `frontend/src/api/{client,types}.ts`; `frontend/src/features/{session,patient,dentist,extraction,audit}/**`; `frontend/src/styles/**`; `frontend/tests/**`; test-only contract mocks under `frontend/src/mocks/**`; `frontend/Dockerfile` if the chosen production build needs one.

**Consumes:** every HTTP shape in `contracts/API_CONTRACT.md`, using local mock handlers while peers implement backends.
**Produces:** the complete responsive UI, a production build and browser smoke tests. No UI component or hidden mock is allowed to decide real access permission.

- [ ] Create labelled demo persona switching and a persistent synthetic-data banner. Use a single API client with cookie credentials, CSRF header, request-ID handling, cancellation, and clear distinction between denied and unavailable.
- [ ] Patient view: own chart, exact notice text/version, recipient/encounter/purpose, unchecked category choices, future expiry, grant confirmation, active/withdrawn/expired history, withdrawal confirmation and effective time. Explain that previously delivered information cannot be recalled.
- [ ] Dentist view: encounter/purpose selection and explicit server request; show only returned allowlisted resources. Display withheld **category labels/reasons**, never their IDs or contents. Show no-grant/expired/withdrawn denial and a retry action without reusing old content.
- [ ] Admin image/review view: one synthetic JPG/PNG, source preview, model ID, editable extraction fields, evidence/uncertainty flags, safe default `restricted`, explicit review checkbox and confirm action. Source preview comes from the selected local file, not a public upload URL. Clear it on persona switch/logout; revoke temporary object URLs.
- [ ] Audit views: patient metadata timeline; admin chain verification and first-broken-link result. No clinical text in timeline rows or tooltips.
- [ ] All views: loading, empty, validation, 401 session expiry, 403 denied, 409 conflict/stale version, 413 size, AI 502/503, ordinary network failure. Prevent duplicate submits. Clear chart/draft caches on logout, persona change, denied response and every new chart read. A stale page must fetch a fresh decision when requesting records again.
- [ ] Keep mock mode explicit (`VITE_API_MODE=mock`), visibly labelled, and restricted to development/test builds. Real mode must surface failures and must never silently fall back to mocked consent/AI success. Mock payloads mirror frozen contract examples.
- [ ] Define `npm run typecheck`, `npm run lint`, `npm run test -- --run`, `npm run build`, and `npm run test:e2e`. Use focused component tests plus browser scenarios, not snapshots of every element.
- [ ] Verify keyboard navigation, labelled fields, focus states, readable contrast, status text beyond color, and layout at 375px and 1280px. Keep screenshots/evidence in P1-owned paths.
- [ ] Test full **mocked** grant → limited chart → withdrawal → denial flow; extraction → edit → confirm; session switching clears another persona's view; AI outage leaves grant/withdraw usable; error response removes old chart. Inspect network response assertions for restricted sentinel absence.
- [ ] Run all five frontend check scripts and `npm run test:e2e` in mock mode. Re-run P1 backend tests. Label browser evidence as mock-backed until final integration runs it against the real API.
- [ ] Commit and push: `feat(p1.2): deliver complete AarogyaShield frontend`.

**Done:** all UI code and tests are delivered together, mock-backed behavior is verified, and `VITE_API_MODE=real` requires no component rewrite. Connecting real routers is reserved for FINAL-INTEGRATION.

## 6. P2 — Consent, deterministic enforcement and filtered chart

**Branch:** `codex/p2-sharing`
**Does not wait for:** P1 sessions or P3 database; inject a fixed server actor and an in-memory transaction fake.
**Deliverable:** policy enforcement and consent transitions tested independently of AI and UI.

### P2.1 — Immutable grant versions, idempotency, list and withdrawal

**Create:** `sharing/{router,schemas,ports,consents}.py`, `backend/tests/p2/{conftest,test_consents}.py`, `backend/requirements/p2.txt`, `docs/handoffs/P2.md`.

**Consumes:** current-actor/CSRF dependencies, clock, notice lookup, encounter lookup and grant repository ports.
**Produces:** `sharing.router.create_router(ports)` and grant/list/withdraw endpoints. Service boundary: `grant_consent(actor, request, uow, now) -> Grant`; `withdraw_consent(actor, grant_id, expected_version, uow, now) -> Grant`.

- [ ] Require patient role and derive patient ID from the actor. Check encounter ownership, seeded recipient assignment, exact purpose `dental-consult`, nonempty permitted category subset, published notice/version/hash, affirmative confirmation, and future UTC expiry.
- [ ] Reject unknown fields/categories, `restricted` as a grant category, naive timestamps, invalid encounter/recipient, expired notice mismatch and cross-patient requests. Choose the documented maximum expiry, not an arbitrary per-handler limit.
- [ ] Store full scope and exact notice snapshot metadata. A new grant is a new immutable row/version; no in-place category widening. Serialize grants per patient as specified in the transaction contract.
- [ ] Key idempotency by patient + endpoint + `idempotency_key`; canonicalize payload categories before hashing. Exact retry returns the same grant without another event. Reused key with different payload returns 409. The key registry stores the original response so a retry after later withdrawal cannot reactivate a grant.
- [ ] Withdrawal is a version-checked transition, writes `withdrawn_at`, and commits its audit event in the same transaction. A repeated withdrawal returns the existing outcome without another event under the documented rules.
- [ ] Tests: `test_exact_retry_same_grant_one_event`, `test_changed_payload_same_key_conflict`, `test_different_category_order_same_retry`, `test_bad_scope_rejected`, `test_wrong_patient_and_role_rejected`, `test_stale_withdrawal_conflict`, `test_withdrawn_grant_never_reactivated`, `test_audit_failure_rolls_back_grant`.
- [ ] Run `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/p2/test_consents.py -q`; update handoff; commit and push `feat(p2.1): add scoped consent lifecycle`.

**Done:** valid grants and withdrawals are atomic, historical and idempotent with fake storage; real transaction behavior is a final integration check.

### P2.2 — Default-deny policy and server-filtered dentist reads

**Create:** `sharing/{policy,chart}.py`, `backend/tests/p2/{test_policy,test_chart}.py`; extend the P2 router only.

**Consumes:** server actor, current grants and encounter metadata.
**Produces:** pure `evaluate_access(actor, encounter, grants, purpose, now) -> Decision`; `read_chart(actor, encounter_id, purpose, uow, now) -> ChartResponse`; chart endpoint in the contract.

- [ ] Check dentist role, assigned recipient, patient/encounter match, exact purpose, active status, starts/expiry and permitted category intersection on **every request**. At `now == expires_at`, deny. No process-local permission cache and no LLM calls.
- [ ] Implement the matching-grant selection rule from the contract; never union unrelated grants. Unknown policy/category or malformed persisted grant fails closed.
- [ ] Authorize before fetching clinical payloads. Select only authorized category rows; construct response fields from an explicit allowlist. Never serialize an ORM object wholesale.
- [ ] Curated `safety_summary` is shared only if separately selected. A dental grant alone cannot reveal allergies/medications through another field, a reason string, evidence span or related draft.
- [ ] A visible encounter with no active matching grant returns 403 and an audited denial; an inaccessible/other-patient encounter returns indistinguishable 404. Return only the constant withheld label `restricted` plus ungranted known scope labels, not hidden record counts/IDs.
- [ ] Write allowed/denied metadata event transactionally before returning; if policy, DB or audit cannot complete, return 503 and no chart. Set `Cache-Control: no-store` on successes and errors.
- [ ] Tests: `test_exact_grant_only_two_safe_resources`, `test_dental_only_excludes_safety`, `test_no_grant_denied_before_resource_fetch`, `test_wrong_recipient_encounter_purpose_denied`, `test_expiry_boundary`, `test_restricted_marker_absent_from_json_and_logs`, `test_audit_error_returns_no_content`.
- [ ] Run the complete P2 suite; commit and push `feat(p2.2): enforce consent on every chart read`.

**Done:** allow/partial/deny behavior and field minimization are proven with explicit payload assertions, independent of frontend filtering.

### P2.3 — Attack cases, post-withdrawal read and real-adapter test specification

**Create:** `backend/tests/p2/{test_adversarial,test_ordering}.py`; extend P2 handoff with the real-database test cases P3 must run at integration.

**Consumes:** completed P2 services with fake ports.
**Produces:** an isolated adversarial suite and exact assertions for real PostgreSQL ordering tests; this subtask does not claim a fake proves database isolation.

- [ ] Add a second patient/encounter/dentist to fake fixtures. Try body actor spoofing, guessed grant IDs, wrong encounter, unknown category, historical grant replay, idempotency races, direct chart/draft URL access and malformed scope.
- [ ] Use a fixed clock to cover starts-at, expiry boundary, two matching grants, latest withdrawn grant versus an older active grant, and a newer explicit re-grant. Follow the documented supersession rule.
- [ ] Prove sequential post-commit behavior: grant → allow → committed withdrawal → same request denied. Verify the resource repository was never called for a denied request.
- [ ] Test transaction rollback when the audit append fails, and database/policy unavailability without returning previously cached resources. Search response/log strings for the restricted sentinel, including validation-error paths.
- [ ] In handoff, specify PostgreSQL tests using **two independent connections** and barriers: a read begun after withdrawal commit denies; overlapping requests serialize according to patient-lock order; simultaneous identical grants create one result/event; simultaneous audit append keeps one chain.
- [ ] Run `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/p2 -q`; report fake-only versus still-pending database checks explicitly.
- [ ] Commit and push `test(p2.3): cover isolation revocation and policy bypasses`.

**Done:** the lane is merge-ready and P3 has executable acceptance details for the real adapter. No real-database test is marked passed until FINAL-INTEGRATION runs it.

## 7. P3 — Persistence, synthetic seed, audit and packaging

**Branch:** `codex/p3-platform-audit`
**Also:** the sole final integrator. This role begins only after all four handoffs are ready.
**Does not wait for:** P1/P2/P4 feature code. Implement the documented storage/transaction ports directly; test with real repositories and narrow test callers.

### P3.1 — Database models, repositories and unit of work

**Create:** `platform/{settings,db,models,repositories,uow}.py`, root package initializer, `backend/tests/p3/{conftest,test_repositories,test_transactions}.py`, `backend/requirements/p3.txt`, `backend/pyproject.toml`, `docs/handoffs/P3.md`.

**Consumes:** entity/port definitions in the companion contract.
**Produces:** `platform.uow.make_uow_factory(settings)`, all `uow` repository methods, and `platform.settings.load_settings()`; feature code must not import concrete ORM classes.

- [ ] Model patients, demo users, sessions, encounters, clinical resources, published notices, consent grants, idempotency results, extraction drafts, audit events and a single audit-head row. Apply patient/encounter foreign keys, explicit category/state constraints, unique idempotency key scope, and unique audit sequence.
- [ ] Store aware UTC times with deterministic round trips and JSON only through constrained service DTOs. Store notice body/version/hash snapshots referenced by a grant; protect published versions from ordinary updates.
- [ ] Implement the exact narrow repository methods and detached dictionaries in the contract. Resource reads must support an explicit category filter so P2 never has to load an entire chart to filter it.
- [ ] Implement `uow_factory(patient_id=...)`: one transaction; lock the patient row before authorization/mutation; fresh read-committed state after obtaining the lock; acquire global audit-head lock only later when appending. All code uses patient-before-audit lock order. On exception, roll back all writes; on normal exit, commit once.
- [ ] For grant/draft lookup before the patient is known, allow a metadata-only lookup outside the write transaction, then reacquire the patient lock and re-read/authorize inside it. Never trust the first lookup as authorization.
- [ ] Test persistence, category-selective queries, rollback, FK constraints, idempotency uniqueness and lock behavior on PostgreSQL. If adding SQLite fallback, serialize its writes explicitly and run the same applicable behavior tests; keep PostgreSQL as required acceptance backend.
- [ ] Run `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/p3/test_repositories.py backend/tests/p3/test_transactions.py -q`; record actual DB backend and test counts.
- [ ] Commit and push `feat(p3.1): add transactional persistence adapters`.

**Done:** real adapters satisfy the documented ports; no feature imports or central router wiring are needed yet.

### P3.2 — Deterministic synthetic scenario, notices and safe seed/reset CLI

**Create:** `platform/{seed,cli}.py`, `platform/seed_data/**`, `backend/tests/p3/test_seed.py`, `docs/operations/seed.md`.

**Consumes:** P3.1 models/repos.
**Produces:** `python -m aarogyashield.platform.cli seed` and `... reset --confirm-demo-reset`; stable IDs and scenario in the companion contract.

- [ ] Seed patient A/B, their separate encounters, dentist A/B, admin and patient personas. Mark every patient/resource as synthetic. Seed one dental item, one curated safety-summary item and one `restricted` item with the exact leak-test marker.
- [ ] Seed English notice `N1`, version `notice-en-1`, with recipient, encounter, `dental-consult`, expiry and withdrawal language. Compute SHA-256 over exact UTF-8 body bytes; expose a copy through P1's notice repository. Keep `restricted` outside selectable scopes.
- [ ] Generate valid relative times using the server clock; do not hardcode an already-expired event-day timestamp. Default seed state has **no grant** so judges can see denial first. Automated allowed-state fixtures may create grants separately.
- [ ] Make seed repeatable without duplicate resources or audit rows. Restrict destructive reset to explicit demo/test mode and a local CLI confirmation flag; reset clears sessions, drafts, grants and audit together with a new documented genesis. Do not add a public reset HTTP route.
- [ ] Tests: `test_seed_twice_stable_counts`, `test_two_patients_isolated`, `test_default_no_grant`, `test_notice_hash`, `test_reset_requires_demo_and_confirmation`, `test_reset_new_chain_genesis`.
- [ ] Run the P3 suite so far; commit and push `feat(p3.2): add repeatable synthetic demo seed`.

**Done:** a fresh local database starts in a known, non-expired synthetic state through one documented command.

### P3.3 — Atomic audit append, timeline, verifier and tamper evidence

**Create:** `audit/{router,schemas,ports,service,canonical}.py`, `backend/tests/p3/{test_audit,test_audit_routes}.py`; extend the CLI with `verify-audit`.

**Consumes:** authenticated actor/CSRF dependencies, P3 audit storage and shared event schema.
**Produces:** `audit.router.create_router(ports)`, `audit.service.append_event(uow, event) -> AuditEvent`, `audit.service.verify_chain(events, expected_head) -> VerificationResult`; `uow.append_audit(event)` delegates to the append function without committing separately.

- [ ] Define a metadata allowlist. Append grant, withdrawal, chart allow/deny, extraction completion/failure and confirmation events without image bytes, draft/source text, clinical summaries, credentials or prompts.
- [ ] Use the exact canonical JSON/hash algorithm in the companion contract. Reserve sequence and link under the audit-head lock in the caller's existing transaction. Avoid an independent connection or premature commit.
- [ ] Verify sequence continuity, canonical event hashes, previous-link correctness, genesis and trusted supplied current-head metadata. Detect tampering, missing/reordered middle events and tail deletion relative to that head. Explain that an administrator who rewrites both chain and head can defeat it.
- [ ] Add patient's own timeline and admin-only verification endpoints. Patient filtering is enforced by current actor; dentist gets no audit dump. Scope patient display fields to metadata and use stable pagination/ordering.
- [ ] Provide a tamper test on a **copy/test DB only**, never a public mutation endpoint or alteration of the real demonstration chain.
- [ ] Tests: `test_clean_chain`, `test_changed_event`, `test_missing_middle`, `test_deleted_tail_against_head`, `test_concurrent_appends_single_chain`, `test_append_rolls_back_with_business_write`, `test_other_patient_history_denied`, `test_payload_rejects_clinical_fields`.
- [ ] Run all P3 tests on PostgreSQL. Commit and push `feat(p3.3): add metadata audit trail and chain verification`.

**Done:** repository transactions create consistent linked events, and API/CLI verification finds the tested corruption cases.

### P3.4 — Runtime packaging, documentation skeleton and integration harness

**Create:** `backend/Dockerfile`, `backend/requirements.txt`, `compose.yaml`, `.env.example`, `.gitignore`, `.github/workflows/checks.yml`, `README.md`, `LICENSE`, `docs/operations/runbook.md`, `platform/health.py`, `main.py`, initial `backend/tests/integration/**` acceptance tests.

**Consumes:** P3's working modules and the other lanes' documented handoff requirements, without importing absent feature modules.
**Produces:** reproducible database/backend harness, safe deployment configuration, and a prepared final acceptance suite. Full app composition remains the final task.

- [ ] Own the central dependency list. During this lane, include only present P3 requirements. Record where P1/P2/P4 requirement files and frontend output will be added after merge; do not create placeholder copies of peer modules or peer-owned files.
- [ ] Build a platform-only `main.py` with liveness/readiness and no clinical endpoints. Keep optional feature wiring out until final integration. A healthy platform harness is not advertised as a working AarogyaShield demo.
- [ ] Prepare Compose services for PostgreSQL and API, volumes, private DB networking and readiness checks. Keep the frontend behind a final-integration profile or add its service only after merge, so missing `frontend/` files do not break this lane's build.
- [ ] `.env.example`: synthetic DB settings, demo mode, session secret placeholder, allowed origin, upload limit, provider mode/model and API-key placeholder. Real secrets live in ignored environment files. Public settings use HTTPS/cookie security; database port is not published publicly.
- [ ] Add test/CI commands with real failures propagated. Run only available P3 paths on this branch; final integration expands checks to all four lanes and frontend. Do not use `continue-on-error`, silent import skipping, or placeholder green tests.
- [ ] Write local startup/seed/reset instructions, an MIT license for team code, implementation-versus-planned table, model/tool disclosure slots and operations/billing ownership. P4 supplies its factual AI section later; do not invent live results or license terms.
- [ ] Author the final acceptance tests against HTTP/contract assertions using fixtures in P3-owned integration paths. Mark them **pending final wiring** in the handoff; a test file existing is not execution evidence.
- [ ] Validate Compose configuration, build/start the platform harness, run seed twice, call health, run audit CLI and P3 tests. Record full-stack checks still pending.
- [ ] Commit and push `chore(p3.4): prepare runtime packaging and integration checks`.

**Done:** storage/audit runtime and documentation skeleton work independently; no teammate code has been merged and no cloud resource is required.

## 8. P4 — Image extraction, reviewer confirmation and AI evidence

**Branch:** `codex/p4-extraction`
**Does not wait for:** frontend, real auth or database. Use a fixed admin actor, fake unit of work and fake provider.
**Deliverable:** safe draft/confirmation APIs, tested provider failures, and honest evidence of the actual model/API integration.

### P4.1 — Validated image ingestion and Gemma draft creation

**Create:** `extraction/{router,schemas,ports,images,provider,service}.py`, `backend/tests/p4/{conftest,test_images,test_provider,test_drafts}.py`, `backend/requirements/p4.txt`, `fixtures/referrals/**`, `docs/handoffs/P4.md`.

**Consumes:** extraction contract, admin actor/CSRF dependency, uow ports and `provider.extract(image_bytes, mime_type, request_id) -> ExtractionResult`.
**Produces:** `extraction.router.create_router(ports)` and `POST /api/extraction-drafts`; `GemmaProvider` plus explicit `FixtureProvider` for tests/offline demonstration.

- [ ] Generate one clearly synthetic referral PNG/JPG and uncertainty/invalid-input fixtures. No real medical document or identifier. Include a visible synthetic label; record provenance rather than importing an earlier team asset as freshly made.
- [ ] Validate admin role before processing. Apply a 5 MiB image-byte limit plus documented multipart overhead limit, PNG/JPEG magic/type checks, successful decode, 16-megapixel decoded limit and EXIF removal. Re-encode before sending; hash the sanitized bytes. Reject SVG/PDF/remote URLs and decompression bombs.
- [ ] Make patient and encounter reviewer-selected, server-validated values. The model receives the sanitized synthetic image and an allowlisted extraction prompt; it cannot choose patient identity, consent state or authorization scope.
- [ ] Implement a backend-only Gemini API call with an image part and configurable Gemma model ID. The SRS proposes `gemma-4-26b-a4b-it`; verify current support with the actual account/API and official documentation. Do not silently substitute Gemini or a different model and claim Gemma challenge compliance.
- [ ] Validate the exact extraction schema, bounded arrays/text lengths, unexpected identifier fields and uncertain fields. Treat source text/image instructions as document content. Do not execute tool requests, URLs, instructions or code from the image/model output.
- [ ] Apply provider timeout and bounded concurrency from the contract. Provider timeout/invalid JSON/API outage returns a visible 502/503 and never mutates consent or publishes a chart resource. Avoid retry loops that duplicate billed calls.
- [ ] Persist only a validated draft and minimal provider metadata. Raw uploads are transient and removed after success/failure; no public file route. AI call happens outside a DB transaction; storing its result/event happens in a short atomic transaction afterwards.
- [ ] Tests: `test_valid_png_and_jpeg`, `test_spoofed_mime_rejected`, `test_over_size_and_pixel_limit`, `test_exif_removed`, `test_invalid_json_no_chart_write`, `test_identity_output_rejected`, `test_provider_timeout_no_consent_change`, `test_image_instruction_cannot_publish`.
- [ ] Run `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/p4 -q`; commit and push `feat(p4.1): add validated multimodal extraction drafts`.

**Done:** fake-backed upload/draft endpoints and the real provider adapter are tested; live availability is separately reported in P4.3.

### P4.2 — Explicit human review and atomic chart publication

**Create:** `extraction/confirmation.py`, `backend/tests/p4/test_confirmation.py`; extend only P4's router/schemas.

**Consumes:** owned draft/version, corrected extraction, patient/encounter binding and approved resource summary/category from reviewer.
**Produces:** `confirm_draft(actor, draft_id, request, uow, now) -> ConfirmationResponse` and the confirmation endpoint.

- [ ] Require demo admin reviewer, correct patient/encounter binding, `human_reviewed=true`, current draft version and editable bounded fields. Display-facing category proposal starts as `restricted`; the backend never infers permission from the AI's confidence.
- [ ] Permit publication only as one resource with a reviewer-authored/approved summary and explicit category. `dental` and `safety_summary` require `category_reviewed=true`; unresolved uncertainty requires `restricted`. No raw `proposed_json`, evidence spans, source text or sensitive mentions are copied into a shared resource.
- [ ] Persist reviewer, review time, corrected fields, category decision, model/prompt version and image hash on the draft. Create the chart item and confirmation audit event in one transaction. No consent is created, widened or reactivated by confirmation.
- [ ] Define repeat confirmation behavior exactly: same expected version plus same canonical corrected payload returns the original resource; changed payload/version after confirmation returns 409. Use uniqueness on `source_draft_id` to prevent concurrent duplicate publication.
- [ ] Tests: `test_unconfirmed_draft_not_in_chart`, `test_non_reviewer_denied`, `test_cross_patient_confirm_denied`, `test_uncertain_defaults_restricted`, `test_only_approved_summary_published`, `test_confirmation_retry_one_resource_one_event`, `test_changed_retry_conflict`, `test_audit_failure_rolls_back_resource`.
- [ ] Run all P4 tests; update handoff with router dependencies/fields. Commit and push `feat(p4.2): require reviewed extraction before chart publication`.

**Done:** explicit approval is the sole publication path, and a newly stored item still needs P2's existing consent rules to become readable by a dentist.

### P4.3 — Real-provider smoke check, honest fallback and model documentation

**Create:** `docs/ai/{model-integration,disclosures}.md`, P4-owned CLI/helper for an opt-in smoke check, and sanitized evidence under `docs/ai/evidence/**`.

**Consumes:** provider adapter, generated fixture, privately configured API key.
**Produces:** exact SDK/model/API configuration, reproducible smoke command, model/terms links, limitations and declared evidence status for P3's README.

- [ ] Check official current Gemini API/Gemma documentation and account capabilities. Record tested model ID, SDK version, date/time, prompt version and image-input support. Do not store the key, authorization headers or full provider debug traffic.
- [ ] Run one real image call if credentials/quota/support allow; record success metadata and a reviewed synthetic response. Assert the outbound request actually includes image bytes and uses the intended model. Mark recorded output as recorded, never live.
- [ ] Test explicit fixture mode with visible `source_mode=fixture`. In live mode, errors remain errors; automatic fallback must not masquerade as a live response. Fixture mode is for an honest local explanation, not proof of challenge eligibility.
- [ ] Document model terms separately from the MIT project license, external data flow to the provider, image retention, timeout behavior, limits, and every AI coding tool used in this lane. Provide P3 README-ready text without editing `README.md` yourself.
- [ ] If missing credentials or unavailable model prevents live proof, finish fake-backed work and mark the live check **BLOCKED** with the exact prerequisite. Do not claim all must-ship requirements are met. Other lanes continue; final acceptance records the AI limitation.
- [ ] Run all P4 tests, then the separate opt-in live smoke command if available. Commit and push `docs(p4.3): document model integration and verified evidence status`.

**Done:** model behavior is documented truthfully, normal tests work offline, and the final integrator knows whether a real multimodal call was verified or remains blocked.

## 9. Parallel schedule and handoff

Use relative time from team kickoff; the supplied SRS's event times are not assumed to be the current clock. Initial 10–15 minutes for everyone: read/freeze contracts, establish the common docs base, and configure separate clones/branches. No application implementation is required before the four lanes start.

| Window | P1 | P2 | P3 | P4 |
| --- | --- | --- | --- | --- |
| Parallel block A, roughly 60–90 min | P1.1 identity/notice | P2.1 consent | P3.1 persistence | P4.1 ingestion/provider |
| Parallel block B, roughly 90–120 min | Begin P1.2 entire frontend | P2.2 chart/policy | P3.2 seed, P3.3 audit | P4.2 confirmation |
| Parallel block C, roughly 45–60 min | Finish/test P1.2 and push | P2.3 attack/ordering tests | P3.4 packaging | P4.3 evidence/docs |
| **Final reserved block, roughly 90–120 min** | Available for P1-owned defects | Available for P2-owned defects | **FINAL-INTEGRATION owner** | Available for P4-owned defects |

These estimates are timeboxes, not a promise. If behind, remove stretch work, simplify visual polish inside P1.2, and prefer local Compose over hosting. Keep authorization tests, withdrawal behavior, reviewed AI boundary and honest disclosure. Freeze contracts before parallel coding; a 15-minute documentation kickoff is not a prerequisite implementation lane.

### Handoff file template — each person owns their own copy

```markdown
# Pn handoff
Branch:
Remote head: resolve the branch head with Git; report its verified SHA in the completion message.
Ready for final integration: YES / NO

## Subtasks
| ID | State | Commit subject(s) or earlier SHA(s) | Push verified | Checks and results |
| --- | --- | --- | --- | --- |

## Interfaces delivered
Router factory, dependency builder, ports implemented/consumed, exact commands.

## Configuration/dependencies
Environment variable names and dependency versions; no secret values.

## Evidence
Command, date/time, backend/provider mode, exit status and test count.
Identify mocked tests, real database tests and real API calls separately.

## Remaining integration checks / blockers
Exact check, responsible owner, prerequisite; NEVER mark as already passed.

## Contract change requests
None, or proposed change plus affected callers and compatibility plan.

## Disclosure
AI tools used and files/work they produced; fixture provenance.
```

An owner's lane is ready when all numbered subtasks have verified pushes, tests pass, files stay within ownership, dependencies/config are described, and the final handoff identifies every remaining integration-only check. A missing real AI check is an explicit blocker to full feature completion, even if the lane can be merged for local testing.

## 10. Coverage map

IDs in this table refer to the **AarogyaShield SRS**, since the older file reuses different FR numbers.

| Requirement | Implementation owner | Final evidence |
| --- | --- | --- |
| FR-01 seed | P3.2 | Fresh DB seed twice, stable scenario |
| FR-02 actor binding | P1.1 + each router's role checks | Spoofed actor, session and second-patient tests |
| FR-03 exact notice | P1.1, P2.1, P1.2 | Notice hash snapshot and unchecked UI |
| FR-04 scoped/idempotent grant | P2.1 | Exact retry/changed retry and DB concurrency tests |
| FR-05 every-read policy | P2.2/P2.3 | No grant, wrong scope, expiry, outage and ordering tests |
| FR-06 minimize fields/safety scope | P2.2, P4.2 | Restricted marker absent from network/logs |
| FR-07 withdrawal | P2.1/P2.3, P1.2 | Real committed withdrawal then immediate denial |
| FR-08 actual Gemma image call | P4.1/P4.3 | Actual model ID, image part and live result or explicit blocker |
| FR-09 review before chart | P4.2, P1.2 | Draft not readable; confirmed approved summary only |
| FR-10 audit/chain | P3.3; business owners append | Clean chain, concurrent append, copied-data tamper |
| FR-11 loading/denial/errors | P1.2, every API owner | Browser states and provider outage flow |
| FR-12 Kannada / FR-13 receipt | Deferred stretch | Added only if must-ship flow already passes |
| NFR-01/02/06/07 security/privacy/reliability/logs | All; P2/P4 boundary tests, P3 transactions | Leakage, rollback, image, secret and DB-failure checks |
| NFR-03 responsiveness | P3 final integration | Measure seeded chart p95 against SRS target <1 second, excluding AI; record actual result |
| NFR-04/05 usability/accessibility | P1.2 | Keyboard, labelled controls, status text, widths |
| NFR-08/09 reproducibility/portability | P3.4 + final task | Fresh clone Compose and same core tests |

Review focus across lanes: cross-patient identifiers, expiry at exact boundary, stale pages after committed withdrawal, uncertain AI text accidentally promoted into shared content, and an audit failure creating an unaudited success. Their explicit tests belong to P1.1/P2.3, P2.2, P1.2/P2.3, P4.2 and P2.1/P3.3 respectively.

## 11. FINAL-INTEGRATION — final task, deferred until all four lanes are ready

**Owner:** P3. **Branch:** `codex/final-integration`. **Status:** NOT STARTED.
**Dependency:** P1.1–P1.2, P2.1–P2.3, P3.1–P3.4 and P4.1–P4.3 handoffs reviewed; blocking limitations explicitly resolved or reported. This task stays last; no owner performs ad hoc cross-branch integration earlier.

### Merge and wire

- [ ] Fetch all four branches, record their handoff commit SHAs and verify pushed heads. Create the integration branch from the original shared base, not from a moving teammate worktree. Merge reviewed branch tips in this order: **P3 → P1 → P2 → P4**, using merge commits and resolving conflicts with the affected owner. Each merge must exit successfully before the next starts.
- [ ] Wire `main.py`: real uow factory, clock/settings, P1 current-actor and CSRF dependencies; mount identity, sharing, audit and extraction routers; select live or explicitly labelled fixture provider; normalize exceptions/request IDs and response headers. Add the feature requirement files to central packaging and the frontend to Compose.
- [ ] Check real adapter signatures against feature Protocols; validate generated OpenAPI and actual responses against the frozen examples. Mock-mode success is not accepted as backend compatibility evidence.
- [ ] Run all four lane suites together, frontend type/lint/unit/build checks and the real-API browser suite. Repair owned logic in the owner's branch; P3 merges the incremental fix. P3 may edit composition/packaging directly but does not silently rewrite another person's feature behavior.

### Acceptance checks — all against the assembled application

- [ ] Fresh clone, private `.env`, `docker compose up --build`, seed twice, health and session checks work using only documented commands. The final README specifies the exact seed container invocation.
- [ ] Patient A cannot inspect B's grants/chart/audit; dentist B cannot use dentist A's grant; actor IDs in bodies cannot override server identity; demo-switch mode and CSRF/session expiry behave as documented.
- [ ] Before grant, dentist gets denial with no chart content. Grant dental + safety: only their allowlisted summaries return. Grant dental alone: safety summary remains withheld. `RESTRICTED_SENTINEL_DO_NOT_SHARE` and restricted resource IDs appear nowhere in dentist JSON, headers, HTML, browser storage or application logs.
- [ ] Withdraw commits; the very next dentist request denies. Test expired/not-yet-valid and wrong-purpose cases. Run P2's two-connection PostgreSQL ordering and concurrent idempotency scenarios; do not substitute fake repositories.
- [ ] Real Gemma image → draft → corrected human review → exactly one published resource, still subject to consent. Invalid image, output mismatch and timeout leave consent/chart unchanged. If the model/API is unavailable, report that the live AI requirement is unmet; clearly labelled fixture mode demonstrates UI only.
- [ ] Grant, read/deny, withdrawal and confirmation events are metadata-only and form a valid chain. Run concurrent append, transaction rollback and copied-chain tamper tests. Confirm verifier limitations are stated accurately.
- [ ] Disable the AI provider: grant/withdraw/chart still work. Disable DB or force audit failure: clinical access fails closed without leaking an older chart. Recheck log/telemetry filters.
- [ ] Browser keyboard flow and 375px/1280px layouts pass with the real backend. Measure at least 30 sequential seeded chart requests, report p95 and setup; compare to the SRS's <1s target without presenting it as a production SLA.
- [ ] Update README with actual working commands, implementation status, fixture/live distinction, license, model/API/terms links from P4, team names, dependencies, synthetic provenance and all AI coding-tool disclosures. Rehearse the five-minute flow.

### Finish

- [ ] If hosting is selected and separately authorized, verify current cost/credit terms and provision one demo environment with HTTPS, private DB access and a named cleanup owner. Keep tested local Compose as fallback. Hosting is not a prerequisite for local acceptance.
- [ ] Push the tested integration branch and prepare the final review/merge. Only the designated integrator merges into `main` under the team's repository policy. No force push or direct feature-owner merge into `main`.
- [ ] Record final commit, test results, demo mode, known limitations and optional deployment URL. Event submission and account actions require their own user authorization; writing this plan does not execute them.

**Final completion criterion:** one assembled, reproducible app passes the real consent/withdrawal/privacy/audit flow, has actual AI evidence or a plainly stated unmet requirement, and has one reviewed integration history. No placeholder, fixture, skipped test or isolated lane result is represented as full-stack success.
