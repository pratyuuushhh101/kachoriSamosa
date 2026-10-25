# Gemma extraction integration

## Current evidence status

**Live smoke status: BLOCKED in the implementation environment.** On 2026-10-25, `GEMINI_API_KEY` was not present. No live API call was attempted, no account capability or quota was verified, and no live model response is claimed. P4.1/P4.2 fake-backed tests do not prove live availability.

Google's current Gemma Gemini API guide lists `gemma-4-26b-a4b-it` as supported and describes image input. It also requires a Gemini API key. That establishes documented capability, not access for this project's Google account. See [Run Gemma with the Gemini API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api).

## Intended configuration

- API: Google Gemini Developer API, through the official `google-genai` Python SDK.
- Default model ID: `gemma-4-26b-a4b-it`; the server may configure `GEMMA_MODEL_ID`, but the live smoke command rejects IDs that do not begin with `gemma-` and verifies the requested ID appears in the prepared outbound request path.
- SDK pin: `google-genai==2.33.0` in `backend/requirements/p4.txt`. This exact SDK was installed into a temporary isolated target and exercised with a mocked HTTP transport; no live request was made.
- Prompt version: `referral-extract-1`.
- Input: the generated synthetic PNG in `fixtures/referrals/synthetic-referral.png`, sanitized/re-encoded and sent inline with the extraction prompt. The smoke observer checks the prepared HTTP request contains the exact sanitized image bytes and the intended model ID without logging or retaining headers/body.
- Limits in the application adapter: 30-second maximum HTTP timeout, two concurrent requests per process, no app retry, and a five-start-per-session-per-minute admission limit in the router. The admission limiter is in-memory and requires one API worker.
- Output: schema-validated JSON stored as an editable admin-only draft. Human confirmation is a separate request. Model output never selects a patient, encounter, consent, or permission.

## Reproduce

Install the lane dependencies in a private virtual environment, then from the repository root:

```bash
PYTHONPATH=backend python -m aarogyashield.extraction.smoke --mode fixture
PYTHONPATH=backend python -m aarogyashield.extraction.smoke --mode live
```

Fixture mode prints `source_mode=fixture` and says that no live model call occurred. It is an offline/demo path, not Gemma evidence. Live mode requires `GEMINI_API_KEY`; optionally set `GEMMA_MODEL_ID` to an account-supported Gemma ID. It never falls back to fixture mode. The command uses only the generated synthetic image, prints only sanitized metadata and a candidate structured response, and returns an error without printing upstream response bodies or credentials. It prompts for the exact word `REVIEWED` before writing a timestamped JSON evidence file with the synthetic response. If no interactive review is confirmed, it writes no live-response evidence.

The key must remain in a private server environment variable or ignored server env file. Do not paste it into a prompt, commit it, or put it in a browser variable. No real patient or referral image may be used in this check.

## Data flow, storage, and limitations

Live mode sends the synthetic PNG bytes and the fixed extraction prompt to Google's Gemini API and receives generated structured text. Local application code keeps raw image bytes transient, stores only the sanitized-image SHA-256 plus the structured draft and minimal model/prompt/source metadata, and exposes no public image URL. The request body and API key are not logged by the smoke helper. Google service-side processing and logging are governed by the account's applicable API terms and settings, not by the local deletion behavior.

Do not send personal, sensitive, confidential, or real health information through an unpaid Gemini API project: Google's terms say unpaid-service prompts and responses may be used to provide, improve, and develop its products and may be reviewed by humans. Paid-service terms state prompts and responses are not used for product improvement, but limited safety logging may still occur. Review the [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms) and [data logging and sharing policy](https://ai.google.dev/gemini-api/docs/logs-policy) for the account's tier and region before any future use. The terms also prohibit using the API for clinical practice or medical advice; AarogyaShield is a synthetic-data demonstration, not a clinical service.

The project license applies to team-authored code only. Google describes Gemma 4's model weights as Apache 2.0 in its [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4); use of the hosted Gemini API is governed separately by Google's API terms, and model weights are not bundled here. The live API account's service terms must be checked independently.

Gemma can misread or omit image text and can emit invalid JSON. A fake provider or recorded response is not a live call. Provider failure is surfaced as an error; the application has no automatic fixture fallback. Review is mandatory, and a dentist still needs the normal consent policy to read an approved resource. This prototype has no clinical validation and is not medical advice.

## README-ready status

> The extraction adapter is implemented for Google's Gemini API with the Gemma 4 model ID `gemma-4-26b-a4b-it`, using `google-genai==2.33.0` and prompt version `referral-extract-1`. The API's official guide documents this model and image input, but the project has not verified live account access: the implementation environment did not contain `GEMINI_API_KEY`, so no live response is claimed. Fixture mode is labeled and is not proof of a live integration. Only generated synthetic images are allowed in the smoke check; results remain drafts until an admin reviews and confirms them.
