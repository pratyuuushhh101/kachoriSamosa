# Open-DPDPA HealthShield — Hackathon-Ready SRS
**Version:** 1.0 · **Date:** 25 October 2026  
**Event:** Hacktoberfest × MOSS Hack Day Udupi  
**Primary targets:** Best Open-Source AI Project + Best Use of Gemma 4  
**License:** MIT (project code; verify each dependency/model's separate terms)

> **Scope decision:** Build a convincing, working vertical slice—not an imaginary enterprise platform. The demo must prove that a patient's granular consent changes what a clinician can see, that the decision is auditable, and that Gemma 4 contributes a real, visible AI capability. Everything else is a clearly labelled extension.

---

## 1. Executive Summary

Open-DPDPA HealthShield is an open-source privacy and consent gateway for healthcare workflows. It demonstrates how a hospital could record patient permissions, evaluate a clinician's request against those permissions, return only the allowed parts of a clinical record, and retain a tamper-evident audit trail of the decision.

### 1.1 Problem
A patient may visit a dentist while their longitudinal record contains unrelated or highly sensitive information. A poorly scoped workflow may expose more information than is needed for that encounter. Hospitals also need a reliable way to show what notice was presented, what permission was given, who requested data, what was disclosed, and whether permission was later withdrawn.

### 1.2 Proposed solution
A lightweight consent-enforcement gateway sits between a demo EHR and a clinician-facing interface. A patient grants or withdraws permission for a purpose/specialty. When a clinician requests a record, the gateway checks the active consent and applies deterministic policy rules before returning data. Gemma 4 helps convert a sample paper consent form or a complex notice into a structured draft and a plain-language patient explanation; the output is reviewed and confirmed rather than trusted blindly.

### 1.3 Product promise
**“The right clinician sees the right health information for the right purpose—and the system can explain and prove why.”**

### 1.4 Hackathon strategy
Design around the published judging rubric: working technical implementation, central and verifiable open-weight AI, thoughtful UX, distinctiveness, usefulness, learning, and a clear demo. The rulebook also requires a public, openly licensed GitHub repository, disclosure of AI coding tools, and a Gemma 4 integration through the Gemini API for the Gemma challenge. Submissions close at **5:00 PM IST**, and the live demo is **5 minutes plus 3 minutes of questions**.

---

## 2. Goals, Non-Goals, and Success Criteria

### 2.1 Goals
1. Demonstrate a patient creating, viewing, and withdrawing a purpose-specific consent.
2. Enforce that consent in a clinician record-request workflow.
3. Show a clear difference between an allowed request, a denied request, and a permitted emergency override.
4. Use Gemma 4 through the Gemini API for one meaningful, visible workflow.
5. Store an auditable event trail with hash chaining and a verification action.
6. Provide a usable web demo, seeded sample data, repeatable setup, and a transparent README.
7. Keep the implementation small enough to complete and explain during a one-day hackathon.

### 2.2 Non-goals for the hackathon MVP
- Production deployment in a real hospital or processing real patient data.
- Claiming legal certification, guaranteed DPDPA compliance, or court-admissible evidence.
- Live integration with ABHA/ABDM, Epic, Cerner, or a real hospital EHR.
- Full support for all 22 scheduled Indian languages, clinical-grade translation, or certified medical transcription.
- Full FHIR conformance, production identity federation, multi-hospital tenancy, or high availability.
- Implementing every scenario listed in either original SRS.

### 2.3 Definition of done
- A user can complete the end-to-end demo without editing the database manually.
- A dentist request is denied or redacted when relevant consent is absent/withdrawn.
- A permitted request returns only the fields allowed by the policy.
- An emergency override requires a reason, is visibly marked, and creates an audit event.
- Audit-chain verification detects a deliberately altered demo event.
- Gemma 4 is called through the Gemini API in the running application; its model name and use are documented.
- The public GitHub repository contains the license, setup instructions, environment example, dependency/model acknowledgements, and AI coding-tool disclosure.
- The deployed demo and local fallback are tested before submission.

---

## 3. Users and Roles

| Role | Purpose | MVP permissions |
|---|---|---|
| Patient | Controls purpose-specific sharing | View sample record, grant/revoke consent, view access history |
| Clinician | Requests data for a defined specialty and encounter | Request records; see allowed data and explanations |
| Hospital privacy administrator | Configures policy and reviews activity | View consent registry, audit log, and chain status |
| Emergency clinician | Requests time-limited emergency access | Submit break-glass reason; receive clearly labelled emergency result |
| Demo/evaluator | Tests the application | Uses seeded demo accounts and sample records |

**Authentication for MVP:** Use seeded demo identities or a simple session-based login. Do not spend the day implementing production-grade identity federation. Never put real patient information in the demo.

---

## 4. Core User Journeys

### Journey A — Grant granular consent
1. Patient opens the consent page.
2. Patient sees a plain-language notice, purpose, requesting clinician/specialty, categories requested, and expiry.
3. Patient grants consent for a defined scope, such as `dental_treatment`, and confirms.
4. The system records the notice version, scope, timestamp, actor, and consent status.
5. The patient sees an active-consent badge and the event in their history.

### Journey B — Clinician requests a record
1. Clinician chooses a patient, specialty, purpose, and encounter.
2. Clinician submits a record request.
3. The policy service checks identity/role, purpose, scope, consent status, and expiry.
4. The gateway returns either an allowed subset or a denial with a human-readable reason.
5. The decision, policy version, resource identifiers, and response hash are added to the audit trail.

### Journey C — Withdraw consent
1. Patient withdraws the dental-sharing consent.
2. The system marks that consent inactive; it does not erase the historical proof event.
3. The clinician repeats the same request.
4. The gateway denies it or returns only fields allowed by another active legal/policy basis explicitly represented in the demo.
5. The UI shows the before/after decision and the withdrawal event.

### Journey D — Emergency break-glass
1. An emergency clinician selects “Emergency access.”
2. The clinician enters a reason and confirms the emergency state.
3. The system grants limited, time-bounded demo access according to a fixed policy.
4. The response is prominently marked **BREAK-GLASS**.
5. The system records actor, reason, time, scope, and result; the patient-facing access history shows the event.

### Journey E — Gemma 4 notice assistant
1. The user selects a provided sample notice or uploads a sample image/PDF if upload support is stable.
2. The backend sends only synthetic/demo content to Gemma 4 through the Gemini API.
3. Gemma 4 drafts a structured representation: purpose, data categories, recipient, duration, withdrawal instructions, and a plain-language summary.
4. The UI displays the source and generated result side by side.
5. The user must review and confirm the draft; it cannot silently create legally effective consent.
6. The app labels the result “AI-generated draft—verify before use.”

---

## 5. Functional Requirements

Priority labels: **P0 = must ship**, **P1 = if time permits**, **P2 = future roadmap**.

### FR-01 — Demo identity and role selection (P0)
- Provide Patient, Clinician, Admin, and Emergency Clinician demo roles.
- Show the active role clearly.
- Enforce role checks on the backend, not only by hiding frontend buttons.
- Seed synthetic users and records on first setup.

**Acceptance:** A clinician cannot call a patient-only consent mutation endpoint.

### FR-02 — Patient and synthetic record view (P0)
- Display a synthetic longitudinal record with categories such as allergies, current medication, dental notes, psychiatric notes, reproductive health, and diagnostic reports.
- Mark every category with a sensitivity/purpose label.
- Include a banner stating that all data is synthetic.

**Acceptance:** The demo record contains at least one ordinary item and two sensitive/unrelated items to demonstrate minimization.

### FR-03 — Consent notice and versioning (P0)
- Show the purpose, recipient/specialty, categories, duration/expiry, and withdrawal route.
- Store a `notice_version` and hash with each grant.
- Make clear that consent is scoped, not a single blanket “agree to everything” toggle.

**Acceptance:** The audit record identifies the exact notice version used at the time of grant.

### FR-04 — Grant, view, and revoke consent (P0)
- Patient can grant and revoke a scope.
- Consent states: `ACTIVE`, `REVOKED`, `EXPIRED`.
- Revocation takes effect for subsequent requests immediately in the MVP.
- Preserve historical events; do not rewrite history to make a revoked consent appear never to have existed.

**Acceptance:** After revocation, repeating the same request yields a different policy decision.

### FR-05 — Policy evaluation and data minimization (P0)
- Evaluate each request using deterministic server-side rules.
- Inputs: requester role, specialty, purpose, patient, encounter, requested categories, consent state, and expiry.
- Return only permitted categories.
- Deny by default if required information is missing or the policy cannot be evaluated.
- Do not let the LLM decide whether access is allowed.

**Acceptance:** A dental request with active dental consent returns dental-relevant information and safety-critical allergies, but excludes unrelated psychiatric/reproductive notes unless the demo policy explicitly authorizes them. Without active consent, the request is denied or minimized according to the configured demo policy.

### FR-06 — Decision explanation (P0)
- Every request returns `ALLOW`, `ALLOW_REDACTED`, or `DENY`.
- Include a short explanation such as “No active consent for dental treatment” or “Psychiatric notes excluded: outside requested scope.”
- Show included and excluded categories in the clinician UI.

**Acceptance:** The explanation matches the actual backend decision and is not generated solely by an LLM.

### FR-07 — Audit trail (P0)
- Record consent grants/revocations, access requests, policy decisions, break-glass events, and AI draft generation.
- Include event ID, timestamp, actor, action, purpose, scope, result, policy version, and relevant hashes.
- Avoid storing full clinical payloads in logs.
- Provide an admin audit view with filters by patient, actor, action, and outcome.

**Acceptance:** The user can trace a record request to the consent state and policy decision used.

### FR-08 — Tamper-evident hash chain (P0)
- Each event stores a hash over a canonical representation of the event plus the previous event hash.
- Provide a “Verify audit chain” action.
- If an event is changed in the demo database, verification reports the first invalid link.
- Describe this as **tamper-evident**, not absolutely immutable. A database administrator with sufficient control may rewrite the entire chain unless additional external anchoring is used.

**Acceptance:** A test modifies a stored event and the verification endpoint fails.

### FR-09 — Emergency break-glass (P1, promote to P0 only if core flow is stable)
- Require emergency role and a non-empty reason.
- Grant only the demo's defined minimum emergency scope.
- Mark all results and audit events.
- Show the access in patient history.
- Do not use this feature to bypass all authorization checks indiscriminately.

**Acceptance:** A normal clinician cannot use the emergency endpoint; a valid emergency request creates a distinct audit event.

### FR-10 — Gemma 4 integration (P0 for Gemma challenge)
- Use the specified Gemma 4 model through the Gemini API, subject to the event's exact model/API availability.
- Provide a backend service wrapper, timeout, error handling, and a safe fallback sample.
- Ask for structured JSON output where supported, then validate it with a schema.
- Treat model output as an untrusted draft; never execute actions or grant consent based only on it.
- Display model name and a clear AI-generated label.
- Keep the API key server-side and out of source control.

**Acceptance:** The running demo can show a successful Gemma response or a clearly identified fallback if the external service is unavailable; the README identifies the actual model/API integration honestly.

### FR-11 — Plain-language notice assistant (P0)
- Transform a complex sample notice into a short, plain-language summary.
- Extract purpose, categories, recipient, duration, and withdrawal method into structured fields.
- Show source text alongside the generated draft.
- Require human confirmation before saving the notice as a usable version.

**Acceptance:** A judge can see what Gemma did and how the result is reviewed.

### FR-12 — Basic admin configuration (P1)
- Allow admin to view configured purposes and category-to-purpose mappings.
- Keep the initial rules in a versioned JSON/YAML file if a UI is too expensive.
- Record the policy version used for each decision.

### FR-13 — Language support (P1)
- Ship English first. Add one locally relevant language only if time allows and the result can be reviewed.
- Do not claim support for all 22 languages unless each is tested.
- Preserve the source notice and show that generated translations require human review.

### FR-14 — FHIR-shaped interoperability (P1)
- Represent the consent record using a small, documented FHIR-inspired structure or a valid FHIR R4 `Consent` resource if the team has tested it.
- Provide a mock FHIR endpoint or export sample JSON.
- Do not claim complete FHIR/ABDM conformance without validation.

### FR-15 — Export and demo reset (P1)
- Export an audit report as JSON.
- Provide a “Reset demo data” action restricted to admin.
- Keep synthetic seed data reproducible.

---

## 6. Non-Functional Requirements

### NFR-01 — Security
- Store API keys in environment variables/secrets, never in frontend bundles or Git.
- Validate request bodies and enforce backend role checks.
- Apply reasonable request size limits and rate limits to public endpoints.
- Use HTTPS for the deployed demo.
- Do not collect real health data, Aadhaar, ABHA identifiers, or other real personal identifiers.

### NFR-02 — Privacy by design
- Use synthetic data only.
- Send only the minimum sample text required to Gemma.
- Do not send clinical records to the model for access-control decisions.
- Avoid logging API keys, full notices containing real identifiers, or full clinical payloads.

### NFR-03 — Reliability
- If the Gemma API is unavailable, consent evaluation and audit features continue to work.
- AI errors must be visible and must not silently become successful consent actions.
- A missing consent record, malformed policy, or unknown purpose must fail closed for ordinary access.

### NFR-04 — Performance
- For the small synthetic dataset, ordinary consent evaluation should feel immediate (target <300 ms server-side, excluding network and AI calls).
- AI generation is asynchronous from the policy path and may take several seconds.
- Do not claim clinical-grade or production throughput based on the hackathon demo.

### NFR-05 — Accessibility and UX
- Responsive interface for laptop and mobile widths.
- Clear status labels, readable contrast, and plain-language denial reasons.
- Use explicit confirmation for grant, revoke, and emergency access.
- Do not rely on color alone to communicate access decisions.

### NFR-06 — Maintainability
- Separate consent logic, policy evaluation, audit logic, and AI integration.
- Use typed request/response schemas.
- Include automated tests for grant, revoke, allow, deny, redaction, role checks, and hash verification.

### NFR-07 — Transparency
- Public repository with an OSI-approved project license.
- Document the actual model, its applicable terms/license, libraries, APIs, datasets, and AI coding tools.
- Distinguish implemented features from mockups, simulations, and roadmap items.

---

## 7. Recommended Architecture

### 7.1 Keep the hackathon architecture simple

```text
Patient / Clinician / Admin Web UI
              |
              v
       FastAPI Application
       ├── Auth / Demo Roles
       ├── Consent Service
       ├── Policy Evaluation Service  <── deterministic rules
       ├── Record Filtering Service
       ├── Audit + Hash-Chain Service
       └── Gemma Adapter             <── Gemini API; never authorizes access
              |
              v
       PostgreSQL (or SQLite locally)
       ├── synthetic_patients
       ├── synthetic_records
       ├── consents
       ├── access_requests
       └── audit_events
```

### 7.2 Suggested stack
- **Frontend:** React + TypeScript + Vite + Tailwind CSS.
- **Backend:** Python FastAPI + Pydantic.
- **Database:** PostgreSQL on DigitalOcean for deployed demo; SQLite as a local fallback if it materially speeds development.
- **AI:** Gemma 4 through the Gemini API, invoked only from the backend.
- **Deployment:** Docker Compose during development; one DigitalOcean App Platform service or a small Droplet for the public demo.
- **Testing:** Pytest for backend logic; Playwright only for one or two critical end-to-end paths if time permits.
- **Interoperability:** FHIR-shaped JSON export or a small tested FHIR `Consent` example—not a full FHIR server for the MVP.

**Do not start with Kafka, Kubernetes, OpenFGA, Keycloak, MinIO, a vector database, a separate model-serving cluster, or a multi-service microservice architecture.** They add setup and failure modes without improving the core 5-minute demonstration. Add one only if the main path is already complete.

### 7.3 Core policy pseudocode

```python
def evaluate_access(request, consent, policy):
    if not request.actor or not request.purpose:
        return deny("Missing actor or purpose")

    if request.actor.role not in policy.allowed_roles:
        return deny("Role not allowed")

    if request.emergency:
        if request.actor.role != "EMERGENCY_CLINICIAN" or not request.reason:
            return deny("Invalid break-glass request")
        return allow(policy.minimum_emergency_categories, label="BREAK_GLASS")

    if consent is None or consent.status != "ACTIVE" or consent.is_expired:
        return deny("No active consent for this purpose")

    allowed = policy.categories_for(
        specialty=request.specialty,
        purpose=request.purpose,
        consent_scopes=consent.scopes,
    )
    if not allowed:
        return deny("Consent does not cover requested data")

    return allow_redacted(allowed, excluded=request.requested_categories - allowed)
```

The real implementation must validate inputs and compute the allowed set on the server. The example is illustrative; do not copy it without adapting the data model and tests.

---

## 8. Data Model

Keep the schema intentionally small.

### `demo_users`
- `id` (UUID)
- `display_name`
- `role`
- `specialty` (nullable)
- `created_at`

### `patients`
- `id` (UUID)
- `display_name` (synthetic)
- `created_at`

### `clinical_records`
- `id` (UUID)
- `patient_id`
- `category` (e.g. `allergy`, `dental`, `psychiatric`, `reproductive`, `medication`)
- `summary` (synthetic text)
- `sensitivity`
- `created_at`

### `consents`
- `id` (UUID)
- `patient_id`
- `recipient_id` or `recipient_scope`
- `purpose`
- `scopes` (JSON array)
- `status`
- `notice_version`
- `notice_hash`
- `granted_at`
- `expires_at`
- `revoked_at` (nullable)

### `access_requests`
- `id` (UUID)
- `patient_id`
- `actor_id`
- `specialty`
- `purpose`
- `requested_categories`
- `decision`
- `included_categories`
- `excluded_categories`
- `reason`
- `policy_version`
- `created_at`

### `audit_events`
- `id` (UUID)
- `sequence_number`
- `event_type`
- `actor_id`
- `patient_pseudonym`
- `event_payload` (minimal JSON)
- `created_at`
- `previous_hash`
- `event_hash`

**Data minimization:** The audit trail should record the decision and hashes, not duplicate the patient's entire medical record.

---

## 9. API Contracts

Prefix: `/api/v1`

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/demo/session` | Return active demo identity/role |
| `GET` | `/patients` | List synthetic patients available to the demo |
| `GET` | `/patients/{id}/records` | Patient view of synthetic record |
| `GET` | `/patients/{id}/consents` | List consent state and history |
| `POST` | `/patients/{id}/consents` | Grant a scoped consent |
| `POST` | `/consents/{id}/revoke` | Revoke active consent |
| `POST` | `/access-requests` | Evaluate and process clinician request |
| `POST` | `/break-glass-requests` | Request emergency access with reason |
| `GET` | `/audit-events` | Filtered audit event list |
| `POST` | `/audit/verify` | Verify the hash chain |
| `POST` | `/ai/notice-draft` | Generate a plain-language/structured draft using Gemma |
| `GET` | `/health` | Health check |

### Example access request

```json
{
  "patient_id": "demo-patient-001",
  "specialty": "dentistry",
  "purpose": "dental_treatment",
  "requested_categories": [
    "allergy",
    "medication",
    "dental",
    "psychiatric",
    "reproductive"
  ]
}
```

### Example response

```json
{
  "decision": "ALLOW_REDACTED",
  "included_categories": ["allergy", "medication", "dental"],
  "excluded_categories": ["psychiatric", "reproductive"],
  "reason": "The active consent and dental policy do not authorize unrelated sensitive categories.",
  "policy_version": "demo-policy-1",
  "audit_event_id": "generated-event-id"
}
```

These examples are contracts for the demo, not official FHIR or legal formats.

---

## 10. UI Requirements

### Screen 1 — Patient privacy home
- Synthetic patient identity and data-use notice.
- Active/revoked consent cards with purpose, recipient, scope, and expiry.
- Clear Grant / Withdraw actions.
- Recent access timeline.

### Screen 2 — Consent detail
- Plain-language notice.
- Requested data categories with short explanations.
- Recipient and purpose.
- Duration/expiry.
- Explicit confirmation and withdrawal route.

### Screen 3 — Clinician workspace
- Select patient, specialty, purpose, and requested categories.
- “Request records” action.
- Result banner: ALLOW / ALLOW REDACTED / DENY.
- Separate visible sections for shared and withheld categories.
- Explain *why* a category was excluded.

### Screen 4 — Admin audit console
- Search/filter audit events.
- Display actor, timestamp, action, purpose, decision, and chain status.
- Verify chain button and clear pass/fail result.
- Show break-glass events prominently.

### Screen 5 — Gemma notice assistant
- Sample notice input.
- Generate draft action.
- Side-by-side source and generated summary/fields.
- Model attribution and “AI-generated; review required” label.
- Confirm/save action separate from generation.

---

## 11. DigitalOcean Deployment and $100 Credit Plan

The team has four credits of $25 each (up to **$100 total**, subject to each credit's validity, account eligibility, and provider terms). Treat credits as a deployment budget, not a reason to overbuild. Check current DigitalOcean prices and credit restrictions before provisioning; prices and eligible products can change.

### 11.1 Recommended deployment
**Best default:** one small application deployment plus managed or bundled database only if needed.
- Deploy the frontend and API as one app/service where practical.
- Use the smallest suitable instance for a synthetic-data demo.
- Use a single PostgreSQL database; SQLite is acceptable for a temporary single-instance demo if persistence/concurrency needs are modest.
- Keep Gemma API calls external via the backend; do not provision a GPU server to run model weights.
- Configure HTTPS, health checks, environment variables, and a simple redeploy path.
- Destroy unused test resources after the event and set billing alerts/limits where available.

### 11.2 Deployment choices
| Option | When to use | Trade-off |
|---|---|---|
| DigitalOcean App Platform | Fastest path to a public demo with low ops overhead | Platform pricing/build limits may apply |
| Small DigitalOcean Droplet + Docker Compose | Familiar, flexible, easy to inspect | Team owns OS updates, firewall, TLS, and deployment reliability |
| Managed PostgreSQL | Need persistent DB without operating it | Extra recurring cost; likely unnecessary for a short demo |
| Local Docker Compose | Development and emergency fallback | Not publicly accessible unless separately exposed |

### 11.3 Budget guardrails
1. Verify live pricing and the credit terms before creating resources.
2. Do not create Kubernetes clusters, load balancers, multiple droplets, GPU instances, or managed services without a concrete need.
3. Use one shared project/account plan and assign one person to monitor billing.
4. Shut down/delete resources that are no longer needed; snapshots, volumes, databases, and reserved IPs may continue to incur charges.
5. Do not put the Gemini API key in the browser. Track API quotas/usage separately from DigitalOcean credits.
6. Keep a local Docker Compose demo ready in case deployment or network access fails.

**Budget target:** keep the hackathon deployment comfortably below the available credit balance; do not assume the credits cover Gemini API usage or every add-on.

---

## 12. Security, Legal, and Clinical Safety Boundaries

- This is an educational prototype, not a legal compliance certification or a production medical system.
- Verify legal section references and implementation obligations against the official current law/rules before making compliance claims.
- Do not assert that a hash chain alone creates a legally admissible or immutable record.
- Do not claim a hospital is an SDF solely from a simple volume questionnaire; formal designation and applicable rules require legal analysis.
- Do not treat consent as the only possible legal basis for every healthcare processing scenario. The demo should clearly label its simplified policy assumptions.
- Do not automatically delete retained medical records or override retention obligations based on a generated AI answer.
- Gemma must not decide access permissions, diagnose patients, or issue legally operative consent.
- Never test with real patient records or identifiable clinical documents.
- All external API data flows must be disclosed in the README and demo.

---

## 13. Testing and Acceptance Plan

### Unit tests — P0
- Active consent + matching purpose → allowed categories returned.
- Missing consent → denied.
- Revoked consent → denied on the next request.
- Expired consent → denied.
- Mismatched specialty/purpose → denied or reduced according to explicit policy.
- Unknown category/purpose → fail closed.
- Unauthorized role cannot grant/revoke consent.
- Break-glass without emergency role/reason → denied.
- Valid break-glass → limited response plus audit event.
- Untampered audit chain → verification passes.
- Modified event → verification fails.
- Gemma API error → no consent mutation; UI shows error/fallback.

### End-to-end test — P0
1. Patient grants dental consent.
2. Dentist requests all sample categories.
3. The app shares dental data and allowed safety-critical information while withholding unrelated sensitive notes.
4. Patient revokes consent.
5. Dentist repeats the request and receives a denial.
6. Admin verifies the audit chain and sees grant, access, and revocation events.

### Demo-readiness checklist
- [ ] Clean install works from README.
- [ ] `.env.example` exists; no secrets are committed.
- [ ] Database seed/reset works.
- [ ] All demo users and synthetic records are labelled.
- [ ] Consent and policy paths work without the AI API.
- [ ] Gemma call works or the fallback is clearly labelled.
- [ ] Public deployment has HTTPS and health check.
- [ ] Public GitHub repo and license are present.
- [ ] All AI coding tools and their contributions are credited.
- [ ] Team can explain the policy engine, data model, model integration, and limitations.

---

## 14. Recommended Build Plan for a One-Day Hackathon

### Phase 1 — Skeleton and one vertical slice
- Create repository, license, README, frontend, backend, and database seed.
- Implement patient consent grant/revoke and the clinician request endpoint.
- Make the dental consent demo work before polishing the UI.

### Phase 2 — Audit and explainability
- Add audit events and hash chaining.
- Add policy explanations and included/excluded category lists.
- Add tests for the core flow.

### Phase 3 — Gemma 4
- Add one backend Gemma integration: notice simplification and structured extraction.
- Validate the model response and require human confirmation.
- Add loading/error states and model attribution.

### Phase 4 — UX and deployment
- Build patient, clinician, and audit screens around the working API.
- Deploy the simplest stable version to DigitalOcean.
- Test from a clean browser and keep a local fallback.

### Phase 5 — Submission and demo
- Freeze feature work before the submission deadline.
- Push the public repository, ensure license/model/tool credits are complete, and submit through OrganizerHQ.
- Rehearse the five-minute working demo and three-minute Q&A.

**Suggested team split**
- Person A: frontend and demo flow.
- Person B: consent API, policy evaluation, and tests.
- Person C: database, audit chain, and deployment.
- Person D (if present): Gemma integration, README, and demo rehearsal.
- Everyone must understand the core request → policy → filtered response → audit path.

---

## 15. Five-Minute Demo Script

**0:00–0:30 — The problem**  
“A patient visiting a dentist should not automatically expose their entire medical history. HealthShield demonstrates purpose-specific access rather than all-or-nothing sharing.”

**0:30–1:20 — Grant consent**  
Show the patient notice, selected scope, and the recorded consent.

**1:20–2:20 — Enforce and minimize**  
As a dentist, request dental, allergy, medication, psychiatric, and reproductive categories. Show the permitted subset and the explicit reason unrelated categories are withheld.

**2:20–3:00 — Withdraw**  
Revoke dental consent and repeat the exact request. Show the denial and the new audit event.

**3:00–3:50 — Gemma 4**  
Use the notice assistant to turn a sample complex notice into structured fields and a plain-language explanation. Show the model attribution and human-review step.

**3:50–4:30 — Audit verification**  
Show the event trail and run hash-chain verification. If prepared, demonstrate a controlled tamper test on local demo data.

**4:30–5:00 — Close**  
Summarize the differentiator: consent is enforced by deterministic policy, Gemma assists with comprehension/structuring, and every decision is traceable. State honestly what is implemented versus simulated.

---

## 16. README and Open-Source Submission Requirements

The event rulebook expects the README to explain the project, list team members, include an open-source license, name each open-weight model with a link to its terms/license, list libraries/APIs/datasets, disclose AI coding tools and the parts they produced, and explain how to run the project. For the Gemma challenge, the README and code/demo must show the Gemma 4 integration through the Gemini API.

Suggested README sections:
1. Problem and solution
2. Screenshots/demo URL
3. Architecture and request flow
4. Features implemented vs. planned
5. Local setup and environment variables
6. Synthetic-data disclaimer
7. Gemma model/API and applicable terms
8. Dependencies, APIs, and licences
9. AI coding-tool disclosure
10. Tests and known limitations
11. Team members and acknowledgements
12. License

---

## 17. Roadmap After the Hackathon

Only pursue these after the MVP is stable:
- A validated FHIR R4 `Consent` resource and conformance tests.
- A real FHIR sandbox connector with a documented capability matrix.
- Open Policy Agent (OPA) for externally managed policies.
- OpenFGA for relationship-based authorization.
- Keycloak/OIDC for real identity federation.
- More reviewed Indian-language notice workflows and accessible voice output.
- External anchoring of audit-chain checkpoints and independent security review.
- Real hospital pilot only after clinical, legal, security, and privacy review.

---

## 18. Final Recommendation

Use **Open-DPDPA HealthShield** as the working name, subject to team agreement. Treat the original long documents as idea banks, not implementation commitments. The winning vertical slice is:

**Scoped consent → deterministic policy enforcement → record minimization → revocation → tamper-evident audit → Gemma-assisted notice explanation.**

This is more credible, demonstrable, and finishable than attempting to build an entire hospital compliance suite in one day.
