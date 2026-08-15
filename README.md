# PhishZero

AI-Powered Email Spam & Phishing Detection System

Project Owner:
Kunal S. Zarodiya

PhishZero is a defensive cybersecurity research application for detecting email spam and phishing. It accepts structured email information or raw `.eml` messages, analyzes text, URLs, and security headers locally, and returns an evidence-based risk classification with explanations.

This project is intended only for authorized defensive research. It does not send email, visit submitted URLs, execute attachments, execute JavaScript from email content, or perform active scanning.

## Problem statement

Email users need a fast way to review suspicious messages without opening attachments, following links, or relying on a single signal. A useful analysis system must combine message text, URL characteristics, authentication headers, and social-engineering indicators while preserving user-data isolation.

## Solution

PhishZero provides:

- Authenticated email ingestion and analysis
- Safe `.eml` parsing with attachment metadata only
- TF-IDF plus Logistic Regression text classification
- Static URL feature extraction with an optional Random Forest model
- Passive SPF, DKIM, DMARC, sender, and Reply-To analysis
- Configurable risk scoring and evidence-based explanations
- A React dashboard for analysis, results, history, and security statistics

## Architecture

```text
React/Vite frontend
        │ Axios + JWT bearer authentication
        ▼
FastAPI API ── Pydantic validation ── Auth/current-user dependency
        │
        ├── Email parser ── text, headers, URLs, attachment metadata
        ├── Text ML ─────── TF-IDF + Logistic Regression
        ├── URL analysis ── static features + optional Random Forest
        ├── Header analysis ─ SPF/DKIM/DMARC and sender consistency
        ├── Risk engine ─── configurable weighted score
        └── Explanation engine ─ evidence and recommended actions
        │
        ├── SQLAlchemy 2.x + SQLite
        └── Alembic migrations
```

Detailed component responsibilities are documented in [`docs/architecture.md`](docs/architecture.md).

## Technology stack

- Frontend: React 18, Vite, Tailwind CSS, React Router, Axios, Vitest
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, SQLite
- ML: pandas, NumPy, scikit-learn, joblib
- Authentication: Argon2 password hashing and environment-configured JWT access tokens
- Testing: pytest, Vitest

## Database design

The database contains `User`, `Email`, `Analysis`, `URL`, `ThreatIndicator`, and `AnalysisFeedback` tables. Foreign keys, ownership predicates, unique constraints, score bounds, severity checks, timestamps, and cascades are defined in the SQLAlchemy model layer.

See [`docs/database.md`](docs/database.md) for the full schema and migration workflow.

## ML architecture

The text model combines email subject and body, normalizes the text, applies TF-IDF, and predicts with Logistic Regression. The URL model extracts static features from the URL string and optionally predicts with a Random Forest. Neither model downloads data automatically.

No trained production artifact is bundled. The CSV files under `backend/tests/fixtures/` are automated-test fixtures only and must not be presented as production training data or accuracy evidence.

Dataset formats and training commands are documented in [`backend/app/ml/README.md`](backend/app/ml/README.md).

## API endpoints

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| GET | `/api/health` | No | Service health check |
| POST | `/api/auth/register` | No | Create a user account |
| POST | `/api/auth/login` | No | Issue a JWT access token |
| GET | `/api/auth/me` | Bearer token | Return the current user |
| POST | `/api/emails` | Bearer token | Parse and store manual or raw email input |
| POST | `/api/analysis` | Bearer token | Analyze and persist an email |
| GET | `/api/analysis/{analysis_id}` | Bearer token | Retrieve one owned analysis |
| GET | `/api/analysis/history` | Bearer token | List the current user’s analyses |

Request and response details are in [`docs/api.md`](docs/api.md).

## Local setup

### Prerequisites

- Python 3.11 or newer
- Node.js compatible with Vite 6 and pnpm
- A generated JWT secret with at least 32 characters

### Backend

From the repository root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
```

Set runtime configuration in the shell or through an approved secret manager. Do not commit `.env` or print secret values.

```powershell
$env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:JWT_ALGORITHM = "HS256"
$env:FRONTEND_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
python -m uvicorn app.main:app --reload
```

The API runs at <http://127.0.0.1:8000>. The health endpoint is <http://127.0.0.1:8000/api/health>.

`.env.example` contains placeholders and non-secret defaults. The application reads environment variables; load `.env` through your approved local environment tooling rather than assuming the server will load it automatically.

### Frontend

In a second terminal:

```powershell
cd frontend
pnpm install
pnpm dev
```

The frontend runs at <http://127.0.0.1:5173> and uses `VITE_API_URL` when provided. Otherwise it calls `http://localhost:8000`.

## Dataset preparation and model training

Training requires an explicitly supplied local CSV. Do not make the application download arbitrary datasets.

Text CSV format:

```csv
subject,body,label
"Meeting reminder","The meeting starts at 10:00.",ham
"Claim your prize","You have won a prize.",spam
```

Train the text model from `backend/`:

```powershell
python -m app.ml.train_text_model --csv C:\path\to\email_dataset.csv
```

URL CSV format:

```csv
url,label
https://www.example.com/account,benign
http://bit.ly/verify-now,phishing
```

Train the URL model from `backend/`:

```powershell
python -m app.ml.train_url_model --csv C:\path\to\url_dataset.csv
```

Training writes artifacts and evaluation metrics under `backend/app/ml/artifacts/`. Review dataset licensing, labels, provenance, and evaluation quality before using any model beyond local research.

## Testing and release checks

Backend tests:

```powershell
cd backend
python -m pytest -q
python -m alembic check
```

Frontend tests and build:

```powershell
cd frontend
pnpm test
pnpm run build
```

The final integration review also verifies backend startup, the health endpoint, explicit-origin CORS, database migrations, and the local frontend preview.

## Docker

No Dockerfiles or Compose files are included in this release. Docker was not available in the verification environment, and adding unverified container infrastructure would introduce deployment assumptions without improving the application itself. Use the native setup above.

If container support is added later, keep the JWT secret outside images, mount SQLite storage deliberately, configure `FRONTEND_ORIGINS` explicitly, and run migrations before serving traffic.

## Security limitations

- The rate limiter is process-local and does not coordinate across workers or hosts.
- SQLite is suitable for local research, not a high-concurrency production deployment.
- Browser bearer-token storage has residual XSS exposure; production deployments should use a hardened session strategy.
- Static URL analysis cannot prove that a destination is safe.
- No trained production model artifacts are bundled, and test fixtures are not production datasets.
- Production deployments still require TLS, filesystem protection, secret management, dependency patching, monitoring, and backups.

See [`docs/threat-model.md`](docs/threat-model.md) for assets, trust boundaries, threats, mitigations, and residual risks.

## Authorized-use statement

Use PhishZero only for defensive cybersecurity research, controlled demonstrations, and systems or email data you are authorized to analyze. Never use it to attack external systems, steal credentials, send spoofed email, execute attachments, visit arbitrary URLs, or perform unauthorized scanning.
