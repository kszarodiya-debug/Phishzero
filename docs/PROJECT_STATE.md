# PhishZero — Project State

## Current Status

Steps 1–14 completed. The final integration review updated the project documentation and verified the application without introducing major new functionality. Steps 5 and 6 remain implemented with no bundled trained artifacts.

## Current Resume Point

PROJECT COMPLETE / MAINTENANCE

## Completed Steps

### Step 1 — Project Foundation

Status:
COMPLETED

Implementation:
- Created the FastAPI backend foundation and React/Vite frontend foundation.
- Added `GET /api/health`, returning the PhishZero service status.
- Configured Tailwind CSS for the frontend.
- Added defensive-cybersecurity project documentation and environment placeholders.

Important files:
- `backend/app/main.py`
- `frontend/src/main.jsx`
- `frontend/src/App.jsx`
- `frontend/tailwind.config.js`
- `.env.example`
- `README.md`

Tests:
- Backend health endpoint verified during application startup checks.
- Frontend production build passes.

Notes:
- The root `README.md` still contains the original foundation-era description and does not fully describe later completed features. It was preserved during this checkpoint.

### Step 2 — Database

Status:
COMPLETED

Implementation:
- Added SQLAlchemy 2.x database configuration for SQLite.
- Added User, Email, Analysis, URL, ThreatIndicator, and AnalysisFeedback models.
- Added primary keys, foreign keys, uniqueness constraints, check constraints, indexes, timestamps, and relationships.
- Configured Alembic and added the initial schema plus subsequent migrations for parsed email fields and analysis risk data.

Important files:
- `backend/app/db/database.py`
- `backend/app/db/models.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/61577913d01b_initial_database_schema.py`
- `backend/alembic/versions/4a8634371dbb_add_parsed_email_fields.py`
- `backend/alembic/versions/b4f2c4d1a9e8_add_analysis_risk_score.py`
- `backend/alembic.ini`

Tests:
- `backend/tests/test_database.py`
- Alembic consistency check is included in checkpoint verification.

Notes:
- The local SQLite file `backend/phishguard.db` exists and is ignored by the project rules.

### Step 3 — Authentication

Status:
COMPLETED

Implementation:
- Added registration, login, and current-user endpoints.
- Validated email and password requirements with Pydantic.
- Hashed passwords using Argon2 through `pwdlib`; plaintext passwords and password hashes are not returned.
- Added JWT access tokens using configuration loaded from environment variables.
- Added a reusable OAuth2 bearer/current-user dependency.
- Enforced authenticated access to the current-user endpoint.

Important files:
- `backend/app/api/auth.py`
- `backend/app/api/dependencies.py`
- `backend/app/core/security.py`
- `backend/app/core/config.py`
- `backend/app/schemas/auth.py`

Tests:
- `backend/tests/test_auth.py` covers registration, duplicate email, login, wrong password, missing and invalid tokens, valid tokens, and current-user retrieval.

Notes:
- JWT configuration is environment-based; no secret is stored in source control.

### Step 4 — Email Ingestion and Parsing

Status:
COMPLETED

Implementation:
- Supports structured manual email input and raw `.eml`/`message/rfc822` uploads.
- Extracts sender, recipients, subject, plain text, HTML, raw headers, URLs, and attachment metadata.
- Limits upload size and validates supported input types.
- Handles malformed messages without exposing raw stack traces.
- Stores parsed email data for the authenticated user.

Important files:
- `backend/app/services/email_parser.py`
- `backend/app/api/emails.py`
- `backend/app/schemas/email.py`
- `backend/tests/test_email_ingestion.py`

Tests:
- Covers plain text, HTML, malformed email, multiple recipients, multiple URLs, and attachment metadata.

Notes:
- Attachments are represented as metadata only. They are not opened or executed.
- URLs are extracted as strings only; the parser does not visit them.

### Step 5 — Email Text ML Model

Status:
COMPLETED WITH ISSUES

Implementation:
- Added subject/body preprocessing, including safe HTML/script/style handling and URL normalization.
- Added explicit local CSV training for TF-IDF plus Logistic Regression.
- Added joblib artifact save/load, probability and confidence output, model versioning, and evaluation metrics: accuracy, precision, recall, F1, and confusion matrix.
- Documented the expected dataset format and training procedure.

Important files:
- `backend/app/ml/preprocess.py`
- `backend/app/ml/train_text_model.py`
- `backend/app/ml/predict.py`
- `backend/app/ml/README.md`
- `backend/tests/fixtures/email_text_fixture.csv`
- `backend/tests/test_ml_text.py`
- `backend/app/ml/artifacts/.gitkeep`

Tests:
- `backend/tests/test_ml_text.py` covers preprocessing, loading, prediction, and missing-model handling.

Notes:
- No trained text model artifact is currently bundled; `backend/app/ml/artifacts/` contains only `.gitkeep`.
- The local fixture is for automated testing and is not a production dataset. No production accuracy claim is made.

### Step 6 — Phishing URL Detection

Status:
COMPLETED WITH ISSUES

Implementation:
- Added URL-string-only static analysis for length, hostname/path length, subdomains, IP presence, `@`, hyphens, digits, special characters, HTTPS, and shortening patterns.
- Added Random Forest URL model training from an explicitly supplied local CSV.
- Added URL classification and probability output.
- Documented the expected dataset format and training procedure.

Important files:
- `backend/app/services/url_analyzer.py`
- `backend/app/ml/train_url_model.py`
- `backend/app/ml/README.md`
- `backend/tests/fixtures/url_fixture.csv`
- `backend/tests/test_url_analysis.py`
- `backend/app/ml/artifacts/.gitkeep`

Tests:
- Covers normal, suspicious, malformed, IP-based, `@`-containing, and long URLs.

Notes:
- No trained URL model artifact is currently bundled; `backend/app/ml/artifacts/` contains only `.gitkeep`.
- The analyzer never visits URLs, crawls websites, downloads content, or performs active scanning.

### Step 7 — Email Header Security Analysis

Status:
COMPLETED

Implementation:
- Parses From, Reply-To, Return-Path, Received, and Authentication-Results headers.
- Reports SPF, DKIM, and DMARC as PASS, FAIL, UNKNOWN, or NOT_PRESENT where evidence is available.
- Detects From/Reply-To mismatch, sender inconsistencies, and authentication inconsistencies.
- Returns structured findings.

Important files:
- `backend/app/services/header_analyzer.py`
- `backend/tests/test_header_analyzer.py`

Tests:
- Covers SPF/DKIM/DMARC pass and fail states, missing authentication headers, and Reply-To mismatch.

Notes:
- Analysis is passive and does not send mail, spoof domains, query DNS, or scan infrastructure.

### Step 8 — Risk Engine

Status:
COMPLETED

Implementation:
- Added a centralized configurable `RISK_CONFIG` with the requested starting weights and thresholds.
- Combines text, URL, header, domain/security, and social-engineering signals.
- Handles missing components without crashing and records errors/missing evidence.
- Returns component scores, detected indicators, calculation details, classification, confidence, and explanation data.

Important files:
- `backend/app/services/risk_engine.py`
- `backend/tests/test_risk_engine.py`

Tests:
- Covers safe, spam-like, suspicious, phishing, missing model, missing URL, missing headers, and conflicting signals.

Notes:
- Missing model artifacts are handled as an unavailable component rather than silently treated as reliable evidence.

### Step 9 — Main Analysis API

Status:
COMPLETED

Implementation:
- Integrated email parsing, text prediction, URL analysis, header analysis, and risk scoring.
- Added authenticated `POST /api/analysis`.
- Persists Analysis, URL, and ThreatIndicator records.
- Added owned-record retrieval and history endpoints.
- Enforces that users can access only their own analysis records.

Important files:
- `backend/app/api/analysis.py`
- `backend/app/schemas/analysis.py`
- `backend/app/db/models.py`
- `backend/tests/test_analysis_api.py`

Tests:
- Covers successful analysis, unauthorized access, invalid input, own-analysis retrieval, cross-user access denial, and history.

Notes:
- API responses include analysis ID, classification, risk score, confidence, component scores, threats, analyzed URLs, and model version.

### Step 10 — Explainable Security Analysis

Status:
COMPLETED

Implementation:
- Added an evidence-based explanation engine returning summary, reasons, and recommended actions.
- Explanations are generated only from actual indicators produced by the analysis system.
- Integrated explanations into analysis API responses.

Important files:
- `backend/app/services/explanation_engine.py`
- `backend/app/api/analysis.py`
- `backend/tests/test_explanation_engine.py`

Tests:
- Verifies that explanations correspond to actual findings and do not invent unsupported evidence.

Notes:
- Recommended actions include avoiding suspicious links, avoiding credential submission, independent sender verification, and reporting/quarantine.

### Step 11 — React Frontend

Status:
COMPLETED WITH ISSUES

Implementation:
- Added React/Vite frontend with Tailwind CSS, React Router, and Axios.
- Added routes for login, registration, dashboard, analysis, results, history, and settings.
- Added Navbar, Sidebar, EmailInput, RiskScore, ThreatCard, AnalysisResult, UrlTable, and SecurityChart components.
- Implemented authentication flow, protected/public routes, API loading/error/empty states, and responsive accessible UI.
- Uses backend API responses rather than hard-coded fake analysis results.
- Added configurable frontend API base URL through `VITE_API_URL`.
- Added backend CORS configuration for local frontend origins to support the integration.

Important files:
- `frontend/src/App.jsx`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/lib/api.js`
- `frontend/src/pages/`
- `frontend/src/components/`
- `frontend/src/index.css`
- `frontend/tailwind.config.js`
- `frontend/package.json`

Tests:
- `frontend/src/components/RiskScore.test.jsx` contains the available Vitest coverage.
- Frontend tests and production build are included in checkpoint verification.

Notes:
- Production build and preview load successfully. In this sandbox, `pnpm dev` encounters an environment-specific Vite/esbuild and pnpm-symlink module-resolution permission failure; this was not treated as an application-code failure.
- Frontend automated coverage is currently limited to the RiskScore component tests.

### Step 12 — Security Dashboard and Analysis UX

Status:
COMPLETED

Implementation:
- Expanded the dashboard to use live `/api/analysis/history` data for total available analyses, safe, low-risk/spam, suspicious, and phishing counts.
- Added live classification distribution bars, average/highest risk, flagged rate, average confidence, and recent analysis cards.
- Added reusable `StatusBadge`, `LoadingState`, and `ErrorState` components.
- Added pure analysis summary utilities and frontend tests for classification and risk statistics.
- Improved the analysis page with client-side sender/recipient/body validation, clear/reset feedback, loading/error states, and safe `.eml` upload through the existing `/api/emails` parser before submission to `/api/analysis`.
- Improved the result page with explicit classification, risk score, confidence, component score bars, threat indicators, analyzed URLs, evidence-based explanations, and recommended actions.
- Improved history with live data, date/subject-equivalent summary, classification, risk, confidence, view-result links, search, and classification filtering.
- Added a small React runtime compatibility fix by importing the existing React namespace in JSX modules; this was required because the current production bundle otherwise rendered a blank page at runtime.

Important files:
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/Analyze.jsx`
- `frontend/src/pages/Results.jsx`
- `frontend/src/pages/History.jsx`
- `frontend/src/components/EmailInput.jsx`
- `frontend/src/components/AnalysisResult.jsx`
- `frontend/src/components/ClassificationChart.jsx`
- `frontend/src/components/StatusBadge.jsx`
- `frontend/src/components/common.jsx`
- `frontend/src/components/SecurityChart.jsx`
- `frontend/src/lib/analysis-utils.js`
- `frontend/src/lib/analysis-utils.test.js`

Tests:
- Frontend Vitest: 7 tests passed.
- Frontend production build passed.
- Browser smoke verification passed for login, dashboard empty/populated states, manual analysis, result rendering, history filtering, logout, and `.eml` extraction/prefill.
- Backend API and full backend suite were preserved; no backend source changes were required.

Notes:
- The dashboard requests up to 100 records from the existing history endpoint because that endpoint does not expose a separate total-count field. Counts are labeled as available history in the UI.
- `.eml` upload first uses the existing safe ingestion endpoint to parse and prefill fields, then submits reviewed fields through the existing analysis endpoint.

### Step 13 — Security Audit and Hardening

Status:
COMPLETED

Implementation:
- Audited authentication, JWT handling, password storage, CORS, authorization, SQLAlchemy queries, XSS boundaries, uploads, EML parsing, request limits, rate limiting, error handling, logging, secret management, and sensitive-data exposure.
- Added JWT algorithm allowlisting for HS256, HS384, and HS512.
- Added fail-fast startup validation for JWT secret, JWT algorithm, frontend origins, and request-size configuration.
- Rejected wildcard credentialed CORS origins and validated explicit HTTP(S) origins.
- Added process-local request-size enforcement with a 6 MiB default and endpoint rate limits for authentication, email ingestion, and analysis.
- Added SQLite foreign-key enforcement for application database connections.
- Added generic 500 error responses without stack traces or internal diagnostic paths.
- Generic application errors log only the request path and exception type; exception messages and tracebacks are excluded from application logs.
- Sanitized risk-engine component error messages so file paths and raw exception input are not returned.
- Added non-secret runtime settings to `.env.example`.
- Created the threat model and security-focused regression tests.

Important files:
- `docs/threat-model.md`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/rate_limit.py`
- `backend/app/db/database.py`
- `backend/app/services/risk_engine.py`
- `backend/tests/test_security_hardening.py`
- `.env.example`

Tests:
- Full backend suite: 72 passed.
- Security-focused tests: 9 passed.
- Frontend suite: 7 passed.
- Frontend production build passed.
- Python compilation, Alembic consistency, API health, and explicit-origin CORS preflight passed.

Notes:
- The rate limiter is process-local and is not a substitute for a shared production gateway limiter.
- The existing frontend bearer-token storage strategy remains a documented residual risk; no token, password, or secret is logged or included in responses.

### Step 14 — Final Integration and Release Preparation

Status:
COMPLETED

Implementation:
- Reviewed the complete backend, frontend, database, authentication, ingestion, ML, header, risk, explanation, API, dashboard, history, and security flows.
- Updated the root project documentation and added architecture, API, and database references based on the actual source tree.
- Documented dataset preparation, explicit model-training commands, testing, native setup, Docker status, security limitations, and authorized use.
- Confirmed no Docker files were added because Docker was unavailable for safe validation and native setup remains the supported release path.

Important files:
- `README.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/database.md`
- `docs/threat-model.md`

Tests:
- Backend suite: 72 passed.
- Security-focused backend tests: 9 passed.
- Frontend suite: 7 passed.
- Frontend production build passed.
- Alembic upgrade/check, Python compilation, backend startup/health, CORS preflight, and frontend preview passed.

Notes:
- The project is complete for the defined 14-step scope. Remaining work is operational hardening and deployment-specific maintenance, not an unimplemented project step.

## Current Architecture

### Frontend

React 18 with Vite, Tailwind CSS, React Router, and Axios. `AuthContext` manages the JWT session, route guards protect authenticated pages, and API-backed pages render a live security dashboard, analysis workflow, results, history, and settings views. Dashboard and history summaries are computed from the existing authenticated analysis history response.

### Backend

FastAPI application in `backend/app/main.py`, with routers for authentication, email ingestion, and analysis. Security middleware enforces request limits/rate limits, startup validates security configuration, and a generic exception handler avoids stack-trace responses. Business logic is separated into services, schemas, core configuration/security, database models, and ML modules.

### Database

SQLite accessed through SQLAlchemy 2.x, with Alembic migrations. The database stores users, parsed emails, analyses, analyzed URLs, threat indicators, and feedback records.

### ML

The text pipeline uses preprocessing, TF-IDF, Logistic Regression, and joblib. The URL pipeline uses static URL features and Random Forest. Both training flows require an explicitly supplied local CSV and do not download datasets automatically.

### API

The API exposes health, authentication, email ingestion, analysis creation, analysis retrieval, and analysis history endpoints. Analysis and history records are ownership-filtered by the authenticated user.

### Authentication

Registration and login use Argon2 password hashing and JWT bearer access tokens. JWT settings are loaded from environment variables. A reusable current-user dependency protects private routes.

### Email parser

The parser accepts manual structured data and raw RFC email input. It safely extracts message fields, URLs, and attachment metadata without executing attachments or visiting URLs.

### URL analyzer

The URL analyzer performs passive string-only feature extraction and optional local-model prediction. It does not make network requests or perform active scanning.

### Header analyzer

The header analyzer performs passive parsing of sender, routing, received, and authentication-result headers, including SPF, DKIM, DMARC, and mismatch findings.

### Risk engine

The risk engine centrally combines model and rule signals using configurable weights and thresholds, with graceful handling for unavailable components.

### Explainability engine

The explanation engine maps only known evidence indicators to summaries, reasons, and recommended actions.

## Current Project Structure

Important current paths include:

```text
phishguard-ai/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/                 # auth, email, and analysis routers
│   │   ├── core/                # configuration and security
│   │   ├── db/                  # SQLAlchemy database and models
│   │   ├── ml/                  # preprocessing, training, prediction, docs
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # parser and security analysis services
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── phishguard.db
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── lib/
│   │   └── pages/
│   ├── package.json
│   ├── index.html
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── pnpm-lock.yaml
├── docs/
│   ├── README.md
│   ├── PROJECT_STATE.md
│   ├── codex-state.md
│   └── threat-model.md
├── ml/                         # reserved top-level project directory
├── .env.example
├── .gitignore
└── README.md
```

The frontend Vite configuration is provided by the current package setup; no additional proxy configuration file is present.

## Database Status

Implemented models and relationships:

- `User` has many `Email` records and many `AnalysisFeedback` records.
- `Email` belongs to `User` and has many `Analysis` records.
- `Analysis` belongs to `Email` and has many `URL`, `ThreatIndicator`, and `AnalysisFeedback` records.
- `URL`, `ThreatIndicator`, and `AnalysisFeedback` each reference their owning analysis through foreign keys.
- `AnalysisFeedback` also references its authoring `User`.

The schema includes indexed foreign keys, unique constraints for user email and per-analysis URL/threat identity, check constraints for bounded scores and supported classifications, and created/updated timestamps where appropriate.

## API Status

Current implemented endpoints:

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/emails`
- `POST /api/analysis`
- `GET /api/analysis/{analysis_id}`
- `GET /api/analysis/history`

Private endpoints require a valid bearer token. Analysis retrieval and history are restricted to the authenticated user’s own records.

## ML Status

### Text model

`backend/app/ml/preprocess.py`, `train_text_model.py`, and `predict.py` implement preprocessing, TF-IDF, Logistic Regression, joblib persistence, probabilities, confidence, and model version output. Training expects a local CSV with documented text/label fields and reports accuracy, precision, recall, F1, and a confusion matrix.

### URL model

`backend/app/services/url_analyzer.py` extracts static URL features. `backend/app/ml/train_url_model.py` trains a Random Forest from an explicitly supplied local CSV and reports classification metrics.

### Artifacts and evaluation

`backend/app/ml/artifacts/` currently contains only `.gitkeep`; no trained text or URL artifact is included. Test fixtures under `backend/tests/fixtures/` are used only for automated tests. The project does not claim production accuracy.

## Security Status

- Passwords are stored only as Argon2-derived hashes.
- JWT configuration is loaded from environment variables; secrets are not hard-coded or logged.
- Pydantic and server-side validation are used for authentication and email inputs.
- Private records are ownership-filtered.
- Email uploads have size/type validation and malformed-message handling.
- Attachments are never executed or opened automatically.
- URLs are never visited, crawled, or actively scanned.
- Email HTML/scripts are parsed as data; JavaScript is not executed.
- Header analysis is passive and does not send mail, spoof domains, attack DNS, or scan infrastructure.
- Explanations are limited to evidence actually produced by the system.
- CORS origins are configurable through `FRONTEND_ORIGINS` with local development defaults.
- JWT algorithms are restricted to approved HMAC algorithms.
- The application fails startup when security-critical JWT/origin configuration is invalid.
- Global request bodies are bounded and selected POST routes are rate-limited.
- SQLite foreign-key enforcement is enabled for application connections.
- Unexpected server errors return generic responses without stack traces or diagnostic paths.

## Known Issues

1. No trained text or URL model artifacts are bundled under `backend/app/ml/artifacts/`; explicit training with a documented local dataset is required for live model predictions.
2. The root `README.md` is stale and still describes the project as if only the foundation step exists. It was intentionally preserved during this checkpoint.
3. No Git repository is present at the project or workspace parent, so branch, commit history, and Git-based working-tree status are unavailable.
4. The Vite development server has an environment-specific failure in this sandbox involving esbuild/PNPM symlink module resolution and permissions. The frontend test command, production build, and preview HTTP check pass.
5. Frontend automated coverage is focused on pure risk/summary utilities; broad page/API integration coverage is not present. Step 12 browser smoke checks cover the main user flow against the live local services.
6. The dashboard can summarize at most the 100 records allowed by the existing history endpoint; no total-count API field is currently available.
7. The process-local rate limiter does not coordinate across multiple workers or hosts.
8. The frontend stores bearer tokens in browser storage; a future XSS issue could expose an active token. A hardened production session strategy is documented in `docs/threat-model.md`.

No additional verified blocking issues found during checkpoint verification.

## Dependencies

### Backend

The current `backend/requirements.txt` includes FastAPI, Uvicorn, SQLAlchemy, Alembic, PyJWT, pwdlib with Argon2 support, email-validator, python-multipart, httpx, pytest, pandas, scikit-learn, joblib, and NumPy.

### Frontend

The current `frontend/package.json` uses React, React DOM, React Router DOM, Axios, Vite, Tailwind CSS, PostCSS, Autoprefixer, and Vitest.

## Testing Status

The following checks were executed during this checkpoint:

- Backend full suite: `backend/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp <unique project-local temp directory>` — 72 passed.
- Security-focused backend tests: `backend/.venv/Scripts/python.exe -m pytest -q tests/test_security_hardening.py -p no:cacheprovider --basetemp <unique project-local temp directory>` — 9 passed.
- Frontend tests: local Node runtime invoking `frontend/node_modules/vitest/vitest.mjs run` — 7 passed across 2 test files.
- Frontend production build: local Node runtime invoking Vite — passed after Step 13 changes.
- Backend Python compilation: `python -m compileall -q app` — passed.
- Alembic consistency: `python -m alembic check` — passed.
- Backend startup and health: Uvicorn started successfully; `GET /api/health` returned HTTP 200 with `status: ok` and `service: phishguard-ai`.
- Frontend preview: served successfully and returned HTTP 200 for `/`.
- Live browser/API smoke flow: login, dashboard, manual analysis, result page, history filtering, logout, and `.eml` parsing/prefill passed against local services.
- Hardened startup/API check: Uvicorn started with an ephemeral runtime secret, health returned HTTP 200, and explicit-origin CORS preflight returned HTTP 200 with the configured origin.

The frontend test/build and service checks above were freshly rerun after the checkpoint documents were created.

## Git Status

- Repository: No Git repository detected at the project directory or workspace parents.
- Current branch: unavailable.
- Latest commit: unavailable.
- Working tree: Git status is unavailable. No reset, revert, checkout, clean, delete, commit, or push operation was performed during this checkpoint.

## NEXT ACTION

The next development task is:

STEP 14 — Final Integration and Release

Future Codex sessions MUST NOT restart from Step 1.
