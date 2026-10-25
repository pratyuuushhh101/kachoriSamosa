# AI and model disclosures

## AI coding tools

- **OpenAI Codex** assisted with P4 extraction implementation, tests, and this documentation. A human project member assigned and reviewed the changes.
- No other AI coding tool was used for this P4 lane.

## Model and service

- Intended model: Google Gemma 4 `gemma-4-26b-a4b-it`, called through the Google Gemini Developer API using the official `google-genai` Python SDK.
- SDK dependency pin: `google-genai==2.33.0`.
- Prompt version: `referral-extract-1`.
- Current evidence: official documentation supports this model ID and image input; the exact pinned SDK prepared a request containing the intended model and exact synthetic image bytes under a mocked transport. Account access and a live call have not been verified because no `GEMINI_API_KEY` was configured in the implementation environment. See [`model-integration.md`](model-integration.md) and [`evidence/p4.3-status.md`](evidence/p4.3-status.md).
- The Gemma 4 model card identifies the model weights as Apache 2.0. The hosted API is a separate service subject to Gemini API terms. The team's MIT code license does not license Google's service or model weights.

## Data and use

The live smoke command is restricted to generated synthetic images. A live request sends the synthetic image and prompt to Google's API; never use actual patient data. The application retains the structured draft and sanitized image hash until demo reset, while the raw upload is transient. Provider timeout is capped at 30 seconds, concurrency at two per process, and no application retry is made. Fixture output is explicitly labeled and is not a live response.

The project is a synthetic hackathon demonstration, not a clinical service, medical advice, or a clinically validated workflow. See Google's [Gemini API terms](https://ai.google.dev/gemini-api/terms) and [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) for external service/model terms.
