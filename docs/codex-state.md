# PhishZero — Codex State

PROJECT: PhishZero
COMPLETED_STEPS: 1-14
NEXT_STEP: MAINTENANCE
TOTAL_STEPS: 14
RESUME_POLICY: Resume from NEXT_STEP
DO_NOT_RESTART: true
DO_NOT_REBUILD_COMPLETED_STEPS: true

## Architecture Summary

PhishZero currently has a React 18/Vite/Tailwind frontend using React Router and Axios, and a FastAPI backend using Pydantic, SQLAlchemy 2.x, SQLite, and Alembic. Authentication uses Argon2 password hashing and environment-configured, algorithm-allowlisted JWTs. The backend supports safe email ingestion/parsing, passive URL analysis, passive email-header analysis, configurable risk scoring, evidence-based explanations, authenticated analysis/history APIs, bounded request sizes, explicit-origin CORS, process-local rate limiting, SQLite foreign-key enforcement, and generic error responses. The frontend includes a live security dashboard, manual and `.eml` analysis workflow, result explanations, history filtering, loading/error/empty states, and responsive risk presentation. Text and URL ML training pipelines use scikit-learn and joblib with explicitly supplied local datasets.

## Important Files

- `backend/app/main.py` — FastAPI application and health route.
- `backend/app/api/` — authentication, email ingestion, and analysis routes.
- `backend/app/db/` — SQLAlchemy database configuration and models.
- `backend/app/services/` — email parser, URL analyzer, header analyzer, risk engine, and explanation engine.
- `backend/app/ml/` — preprocessing, training, prediction, and ML documentation.
- `backend/tests/` — backend test suite and local test fixtures.
- `frontend/src/` — routes, pages, components, authentication context, and API client.
- `frontend/src/lib/analysis-utils.js` and `frontend/src/components/ClassificationChart.jsx` — Step 12 dashboard summaries and distribution visualization.
- `frontend/src/components/StatusBadge.jsx` — reusable classification state presentation.
- `backend/app/main.py` — security middleware, startup validation, CORS, error handling, and API entrypoint.
- `backend/app/core/config.py` and `backend/app/core/rate_limit.py` — security configuration validation and throttling.
- `backend/tests/test_security_hardening.py` — Step 13 security regression tests.
- `docs/threat-model.md` — assets, trust boundaries, threats, mitigations, and residual risks.
- `.env.example` — non-secret environment placeholders.
- `README.md` — project overview, setup, training, testing, Docker status, and authorized-use guidance.
- `docs/architecture.md` — current component architecture and analysis flow.
- `docs/api.md` — implemented endpoints, contracts, and error behavior.
- `docs/database.md` — current schema, relationships, migrations, and data handling.
- `docs/PROJECT_STATE.md` — detailed human-readable checkpoint and verification record.

## Resume Guardrails

Steps 1–14 are completed work and must be preserved. The project is now in maintenance/release state. Do not restart from Step 1 or rebuild completed steps unless a future task explicitly identifies and authorizes a narrowly scoped bug fix.
