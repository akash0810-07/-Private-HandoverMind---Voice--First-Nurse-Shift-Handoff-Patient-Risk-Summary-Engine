# HandoverMind — Voice-First Nurse Shift Handoff & Patient Risk Summary

> **Academic demonstration system — uses synthetic patient data only.**
> This is a B.Tech CSE academic project (Healthcare / Medical AI). It is an
> **AI-assisted documentation and summarisation tool** — it does **not**
> diagnose, prescribe, or recommend treatment, and it never writes into a
> real hospital EHR. A qualified nurse reviews and confirms every
> AI-generated summary before it is treated as reliable.

---

## 1. Problem statement

Nurses hand off patient information between shifts through rushed verbal
conversation, sticky notes, or scattered EHR entries — and details like
medications, vital trends, pending tests, allergies, and deterioration can
get lost. HandoverMind lets an outgoing nurse simply **speak** the handoff.
The system transcribes it, extracts structured per-patient information,
flags potential risk indicators, and surfaces high-risk patients first on
the incoming nurse's dashboard — with every AI output subject to human
review before it's treated as confirmed.

## 2. Features

- Voice recording in the browser → upload → transcription
- AI structured extraction into a strict per-patient JSON schema
- Hybrid (rule-based + AI) risk detection with explainable evidence
- Risk-sorted dashboard (High → Medium → Low), search/filter/sort
- Human-in-the-loop review: edit, then explicitly confirm, every summary
- JWT auth, role-based access (NURSE/ADMIN), ward-level data isolation
- Full observability of every AI call (provider, model, latency, retries)
- Dockerized, CI/CD via GitHub Actions, deployment-ready

## 3. Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full pipeline
diagram, provider abstraction, validation/retry logic, hybrid risk scoring,
security model, ER diagram, and CI/CD design. Summary of the AI pipeline:

```
Mic → Upload → STTProvider → Transcript → LLMProvider (strict JSON)
    → Pydantic validation (retry on failure, never store malformed data)
    → RiskDetectionService (rules + AI, hybrid, evidence-preserving)
    → PatientSummary (PENDING_REVIEW) → Nurse edits/confirms → CONFIRMED
```

AI is a first-class, swappable part of the architecture (`STTProvider`,
`LLMProvider` interfaces) — not hardcoded to one vendor, and not faked.

## 4. Tech stack

**Frontend:** React, React Router, browser MediaRecorder API, Vite, Playwright
**Backend:** Python, Flask, SQLAlchemy, Flask-JWT-Extended, Pydantic/Marshmallow, Pytest
**Database:** PostgreSQL (prod/Docker) / SQLite (local dev fallback)
**AI:** OpenAI Whisper (STT) + OpenAI Chat Completions (LLM), pluggable, mock providers for offline dev/CI
**Infra:** Docker, Docker Compose, GitHub Actions CI/CD, Nginx (frontend serving)

## 5. Database schema

See §8 of [`docs/architecture.md`](docs/architecture.md). Core entities:
`Ward`, `Nurse`, `HandoffRecording`, `ProcessingJob`, `PatientSummary`,
`RiskFlag`, `AuditLog`, `AIProcessingLog`. All UUID primary keys, all
timestamped.

## 6. API documentation

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | Login, returns access + refresh JWT |
| POST | `/api/auth/refresh` | Rotate access token |
| POST | `/api/auth/logout` | Revoke current token |
| GET | `/api/auth/me` | Current nurse profile |
| POST | `/api/handoff/record` | Upload audio, runs full AI pipeline |
| GET | `/api/handoff/:id/summary` | Recording + its patient summaries |
| GET | `/api/handoffs` | Paginated handoff history (ward-scoped) |
| GET | `/api/patients` | Search/filter/sort patient summaries |
| GET | `/api/patients/flagged` | High/medium risk, high-risk first |
| GET | `/api/patients/:id` | Single patient summary |
| PATCH | `/api/summaries/:id` | Nurse edits an AI-generated summary |
| POST | `/api/summaries/:id/confirm` | Human confirmation (required) |
| GET | `/api/jobs/:id` | AI processing job status (for polling) |
| GET | `/api/dashboard/stats` | Dashboard counters |
| GET/POST | `/api/admin/wards` | Ward management (ADMIN) |
| GET/PATCH | `/api/admin/nurses...` | Nurse/ward assignment (ADMIN) |
| GET | `/health`, `/ready` | Liveness / readiness |

All responses use consistent JSON error shapes (`{"error": "...", "message": "..."}`)
and correct HTTP status codes; every non-auth route requires a valid JWT and
is ward-scoped unless the caller is ADMIN.

## 7. Local setup (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env      # then edit values as needed
flask --app wsgi.py init-db
python ../scripts/seed_data.py
flask --app wsgi.py run --debug   # http://localhost:5000

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Demo logins (created by `seed_data.py`):
- Nurse: `nurse.demo@handovermind.test` / `DemoPass123!`
- Admin: `admin.demo@handovermind.test` / `DemoAdminPass123!`

## 8. Environment variables

See [`.env.example`](.env.example) for the full list. Key ones:

| Variable | Purpose |
|---|---|
| `SECRET_KEY`, `JWT_SECRET_KEY` | Flask/JWT signing secrets — set real random values, never commit |
| `DATABASE_URL` | Postgres (Docker) or SQLite (local fallback) |
| `STT_PROVIDER` | `mock` (offline) or `whisper_api` (real, needs `OPENAI_API_KEY`) |
| `LLM_PROVIDER` | `mock` (offline) or `openai` (real, needs `OPENAI_API_KEY`) |
| `OPENAI_API_KEY` | Server-side only; never exposed to the frontend |
| `CORS_ORIGINS` | Allowed frontend origin(s) |

## 9. Docker setup

```bash
cp .env.example .env    # edit as needed; POSTGRES_PASSWORD must match here
docker compose up --build
# backend:  http://localhost:5000
# frontend: http://localhost:5173
```

First run: seed data inside the backend container —
`docker compose exec backend flask --app wsgi.py init-db`
`docker compose exec backend python ../scripts/seed_data.py`

## 10. Running tests

```bash
# Backend (Pytest, uses mock AI providers — no external API calls or keys needed)
cd backend
pytest --cov=app --cov-report=term-missing

# Frontend E2E (Playwright)
cd frontend
npm install
npx playwright install --with-deps
npm run build && npx playwright test

# AI evaluation harness (deterministic synthetic transcripts)
cd backend
python ../scripts/evaluate_ai_pipeline.py
```

## 11. CI/CD

GitHub Actions (`.github/workflows/`):
- **`ci.yml`** — on every push/PR: lint → backend Pytest+coverage → frontend
  build → Playwright E2E (against a seeded SQLite instance with mock AI
  providers) → Docker build (both images) → dependency/container security
  scan (pip-audit, npm audit, Trivy). Failing any stage fails the pipeline.
- **`cd.yml`** — on a successful CI run on `main`: builds & pushes both
  images, deploys (adapt the placeholder step to your target platform),
  runs a retrying `/health` check, and rolls back on failure.

Configure these **GitHub Secrets** before enabling CD: `REGISTRY_URL`,
`REGISTRY_USERNAME`, `REGISTRY_PASSWORD`, `DEPLOY_HOST`, `DEPLOY_SSH_KEY`,
`PRODUCTION_API_BASE_URL`. Database/JWT secrets are set as environment
variables on the deploy target itself, never committed.

## 12. Deployment instructions

1. Provision Postgres and set `DATABASE_URL` on the target host/platform.
2. Set `SECRET_KEY`, `JWT_SECRET_KEY`, `OPENAI_API_KEY` (if using real AI
   providers) as platform secrets/env vars — never in source control.
3. Push both Docker images (done automatically by `cd.yml`), or build on
   the host with `docker compose -f docker-compose.yml up -d --build`.
4. Point your load balancer / reverse proxy health check at `GET /health`
   (liveness) and `GET /ready` (readiness, checks DB connectivity).
5. Run `flask --app wsgi.py init-db` (or Alembic migrations, if you've
   run `flask db init && flask db migrate` for schema evolution) once
   against the production database.

## 13. AI provider configuration

Set `STT_PROVIDER=mock` / `LLM_PROVIDER=mock` for a fully offline demo —
no API keys, deterministic output, safe for CI. To use real AI:

```
STT_PROVIDER=whisper_api
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
WHISPER_MODEL=whisper-1
```

No code changes are required — `app/services/ai/factory.py` selects the
implementation at runtime from these environment variables.

## 14. Demo workflow

1. Log in as the demo nurse.
2. Go to **Start Handoff** → record (or, in mock mode, just stop
   immediately — a synthetic sample transcript is used).
3. Watch the processing stages (Uploading → Transcribing → Analysing →
   Structuring → Risk detection → Ready for review).
4. Land on the AI summary — note the **"AI-generated summary — review and
   confirm before use"** banner and per-flag **"Potential risk indicator
   detected in handoff"** language.
5. Edit a field if needed, then **Confirm**.
6. Return to the **Dashboard** — the patient now appears sorted by risk,
   with review status visible.

## 15. Viva / evaluation explanation

Be ready to explain, with the code open:
- Why the AI layer is an abstraction (`STTProvider`/`LLMProvider`) rather
  than a direct API call — swappability, testability without secrets.
- Why risk detection is **hybrid**, not LLM-only — `rules_config.py` is a
  deterministic, explainable safety net; the AI adds contextual recall.
- Why malformed AI output is retried then rejected, never stored
  (`AIProcessingPipeline._extract_with_retries`, Pydantic validation).
- Why every summary starts `PENDING_REVIEW` and needs an explicit
  `confirm` call — human-in-the-loop is enforced at the data-model level,
  not just the UI.
- How ward-level authorization prevents cross-ward data access
  (`ward_access_required`, tested in `test_review_workflow.py`).
- The CI/CD flow: `git push` → lint/tests → Playwright E2E against a
  seeded mock-AI instance → Docker build → security scan → deploy →
  health check → rollback on failure.

## 16. AI safety limitations (read this)

- This system **does not diagnose disease, prescribe medication, or
  recommend treatment**, and it does not automatically write into any
  hospital EHR.
- All risk output is labeled "**Potential risk indicator detected in
  handoff**," never "AI diagnosis" or "AI treatment recommendation."
- Every AI-generated summary is labeled "**AI-generated summary — review
  and confirm before use**" and requires explicit nurse confirmation.
- The mock LLM/STT providers are simple, transparent heuristics for
  offline development and grading — they are not presented as, and should
  not be mistaken for, real clinical NLP or speech models.
- Do not connect this system to real patient data. It is built and tested
  against **synthetic/fictional data only** (`scripts/seed_data.py`).

## 17. Synthetic data policy

All wards, nurses, patients, and transcripts used anywhere in this
repository (seed script, tests, evaluation harness, demo) are fictional,
generated with `Faker`. No real patient information is used or stored.

## 18. Project limitations

- AI pipeline runs synchronously per request (see `docs/architecture.md`
  §2) rather than via a background worker — acceptable for the academic
  v1 scope; the upgrade path to Celery/RQ is documented.
- Token revocation is in-memory (single process) — use Redis for a real
  multi-instance deployment.
- English only; no hospital EHR write-back; no diagnosis/treatment
  features — all intentionally out of scope for v1 (see §30 of the
  original spec / `docs/architecture.md` §11).

## 19. Future improvements

Multilingual support, real-time streaming transcription, FHIR
interoperability, hospital EHR integration, a native mobile app, more
advanced clinical NLP, and richer analytics on review/edit rates — kept
architecturally possible (provider abstractions, modular services) but
intentionally not built in v1.

## 20. Project structure

```
handovermind/
├── frontend/            React app (Vite, Playwright tests)
├── backend/              Flask app (app/, tests/)
│   └── app/
│       ├── api/          REST blueprints
│       ├── auth/         JWT + RBAC + ward-scoping
│       ├── models/       SQLAlchemy models
│       ├── schemas/      Pydantic (AI output) + Marshmallow (API input)
│       └── services/
│           ├── ai/       LLMProvider, prompts, pipeline orchestrator
│           ├── stt/      STTProvider (mock + Whisper)
│           ├── risk/     Hybrid risk detection + configurable rules
│           └── storage/  Storage backend abstraction
├── scripts/              seed_data.py, cleanup_recordings.py, evaluate_ai_pipeline.py
├── docs/architecture.md  Full architecture, ER diagram, CI/CD design
├── .github/workflows/    ci.yml, cd.yml
├── docker-compose.yml
└── .env.example
```
