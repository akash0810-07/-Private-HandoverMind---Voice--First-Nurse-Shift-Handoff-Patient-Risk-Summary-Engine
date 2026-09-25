# HandoverMind — Architecture

## 1. System overview

```
Browser (React)                Flask API                 AI Providers
──────────────                 ─────────                 ────────────
Record mic audio  ───POST───▶  /api/handoff/record
                                    │
                                    ▼
                              Storage backend (local/S3)
                                    │
                                    ▼
                              STTProvider.transcribe()  ───▶  Whisper API / mock
                                    │
                                    ▼
                              LLMProvider.generate_json() ─▶  OpenAI / mock
                                    │
                                    ▼
                              Pydantic schema validation (retry on failure)
                                    │
                                    ▼
                              RiskDetectionService (rules + AI, hybrid)
                                    │
                                    ▼
                              PatientSummary + RiskFlag rows (PENDING_REVIEW)
                                    │
                                    ▼
                              Nurse reviews/edits  ───PATCH/POST──▶ CONFIRMED
```

## 2. Why the pipeline runs synchronously in v1

The spec calls for asynchronous-style processing with job states
(QUEUED → TRANSCRIBING → ANALYSING → RISK_DETECTION → COMPLETED/FAILED).
For the academic v1 scope, `AIProcessingPipeline.run()` executes these
stages inline within the request, updating the same `ProcessingJob` row a
worker-based system would use. This keeps the deployment footprint small
(no broker/worker infra required) while preserving:

- the exact same state machine and API contract (`GET /api/jobs/:id`)
- the exact same frontend polling code path
- a straightforward upgrade path: swap the call in `app/api/handoff.py`
  for `pipeline.run.delay(...)` on a Celery/RQ worker without touching the
  pipeline internals, models, or frontend.

## 3. AI provider abstraction

`STTProvider` and `LLMProvider` are abstract interfaces
(`app/services/stt/base.py`, `app/services/ai/base.py`). Concrete
implementations:

| Provider | Class | Notes |
|---|---|---|
| STT (offline) | `MockSTTProvider` | Deterministic canned transcripts, hashed from input bytes. Safe for CI/demo, no network. |
| STT (real) | `WhisperSTTProvider` | OpenAI Whisper API. Requires `OPENAI_API_KEY`. |
| LLM (offline) | `MockLLMProvider` | Regex/heuristic structured extraction. Transparent, not presented as a real clinical NLP model. |
| LLM (real) | `OpenAILLMProvider` | OpenAI Chat Completions, JSON mode. Requires `OPENAI_API_KEY`. |

Selection is via `STT_PROVIDER` / `LLM_PROVIDER` env vars, resolved in
`app/services/ai/factory.py`. No other module imports a concrete
provider directly.

## 4. Structured output contract & validation

The LLM must return JSON matching `HandoffExtractionResult`
(`app/schemas/ai_schema.py`, Pydantic). If the JSON is malformed or fails
validation, `AIProcessingPipeline._extract_with_retries` retries up to
`AI_MAX_RETRIES` times, logging every attempt to `AIProcessingLog`. If all
retries fail, the pipeline raises `AIProcessingError`, the job/recording
are marked `FAILED`, and **nothing malformed is ever persisted** as a
patient summary.

## 5. Hybrid risk detection

`RiskDetectionService` (`app/services/risk/detection_service.py`) never
relies solely on the LLM:

1. **Rule-based layer** (`rules_config.py`) — configurable regex rules
   with severity weights, run directly against the transcript so matches
   are deterministic and evidence-backed.
2. **AI layer** — contextual `risk_indicators` from the LLM extraction.
3. **Aggregation** — indicators found by both layers are merged and
   tagged `HYBRID`; total severity weight maps to LOW/MEDIUM/HIGH via
   configurable thresholds; the AI's own `risk_level` can escalate (never
   de-escalate) the final level, since it may catch context a keyword
   rule misses.

Every `RiskFlag` stores `source` (`RULE`/`AI`/`HYBRID`) and, where
available, the verbatim transcript `evidence` — this is what makes the
output explainable to the reviewing nurse.

## 6. Human-in-the-loop

`PatientSummary.review_status` starts at `PENDING_REVIEW`.
`ai_original_payload` freezes the untouched AI output. `PATCH
/api/summaries/:id` lets a nurse edit any field; `POST
/api/summaries/:id/confirm` sets `review_status=CONFIRMED`,
`reviewed_by_id`, `reviewed_at`. A summary is never presented as final
without this explicit step.

## 7. Security & access control

- JWT auth (`Flask-JWT-Extended`), bcrypt password hashing, access +
  refresh tokens, in-memory revocation list on logout (documented as a
  simplification for v1 — a multi-instance deployment should use Redis).
- `roles_required(...)` and `ward_access_required(...)` decorators
  enforce RBAC and ward-level data isolation on every ward-scoped route.
- File upload validation: extension allow-list + `MAX_CONTENT_LENGTH`.
- Rate limiting on login and recording upload (`Flask-Limiter`).
- Generic error handlers never leak stack traces.
- Security headers set on every response (`X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy`).
- No secret is ever sent to the frontend or logged; `OPENAI_API_KEY` is
  read only server-side from the environment.

## 8. Database schema (entities)

```
Ward 1───* Nurse
Ward 1───* HandoffRecording 1───1 ProcessingJob
HandoffRecording 1───* PatientSummary 1───* RiskFlag
Nurse 1───* AuditLog (actor)
HandoffRecording 1───* AIProcessingLog
```

All primary keys are UUID strings; all tables carry `created_at` /
`updated_at`. See `backend/app/models/` for the SQLAlchemy definitions.

## 9. Observability

Every STT/LLM call is logged to `AIProcessingLog` with request id,
stage, provider, model, duration, token usage (if available), retry
count, and validation result — never secrets. `scripts/evaluate_ai_pipeline.py`
runs a small deterministic eval set and prints accuracy/recall/latency
metrics for the current provider configuration.

## 10. CI/CD

`.github/workflows/ci.yml`: lint → backend Pytest → frontend build →
Playwright E2E (against the app running with mock AI providers and
seeded SQLite data) → Docker build (both images) → dependency/container
security scan (pip-audit, npm audit, Trivy).

`.github/workflows/cd.yml`: triggered on a successful CI run on `main`;
builds and pushes both images, deploys (placeholder step — fill in your
target platform's deploy command), runs a `/health` check with retries,
and rolls back to the `:stable` tag if the health check fails.

## 11. Known limitations (v1)

- AI pipeline runs synchronously per-request rather than via a background
  worker (see §2 for the rationale and upgrade path).
- Token revocation is in-memory (single-process); use Redis for a
  multi-instance production deployment.
- No hospital EHR write-back, diagnosis, or treatment recommendation —
  intentionally out of scope (see README "Project limitations").
- English only in v1.
