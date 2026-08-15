# PhishZero Database

## Technology and migrations

The application uses SQLite through SQLAlchemy 2.x. Alembic owns schema migrations. From `backend/`, apply the current schema with:

```powershell
python -m alembic upgrade head
python -m alembic check
```

The default local database is `backend/phishguard.db`. `DATABASE_URL` can point to another SQLAlchemy-compatible database URL, but SQLite is the supported local configuration.

## Tables

### `users`

Stores the user identity and an Argon2-derived `password_hash`. It never stores plaintext passwords. Email is unique and indexed. `created_at` and `updated_at` provide audit timestamps.

### `emails`

Stores one parsed email owned by a user:

- sender and recipient string values
- subject, plain-text body, and optional HTML body
- JSON raw headers
- JSON extracted URLs
- JSON attachment metadata
- optional message ID and received timestamp

`user_id` is a foreign key to `users.id` with cascade deletion.

### `analyses`

Stores one risk-engine result for an email:

- `classification`: `SAFE`, `LOW_RISK`, `SUSPICIOUS`, or `PHISHING`
- `verdict`: internal safe/spam/suspicious/phishing state
- bounded `risk_score` and `confidence`
- JSON component scores
- model version
- serialized explanation and analysis timestamp

`email_id` references `emails.id` with cascade deletion.

### `urls`

Stores URL strings derived from an analysis, with optional domain, verdict, and bounded risk score. `(analysis_id, url)` is unique. URL records are never used to perform network requests.

### `threat_indicators`

Stores detected evidence such as suspicious URL characteristics, header failures, and social-engineering indicators. Severity is restricted to `low`, `medium`, `high`, or `critical`. `(analysis_id, indicator_type, value)` is unique.

### `analysis_feedback`

Stores optional user feedback for an analysis. Each user can provide at most one feedback record per analysis through the database uniqueness constraint. Both user and analysis foreign keys cascade on deletion.

## Relationships

```text
User 1 ──── * Email 1 ──── * Analysis
User 1 ──── * AnalysisFeedback * ──── 1 Analysis
Analysis 1 ──── * URL
Analysis 1 ──── * ThreatIndicator
```

SQLAlchemy relationships use ownership-aware cascades and the SQLite engine enables `PRAGMA foreign_keys=ON` for application connections.

## Constraints and indexes

- User email uniqueness and minimum lengths
- Password-hash minimum length
- Bounded analysis scores and confidence
- Supported classification, verdict, URL verdict, and threat severity values
- Indexed user, email, analysis, URL-domain, and foreign-key columns
- Unique per-analysis URL and threat identity
- Cascading foreign-key deletion for dependent records

## Sensitive data handling

Email bodies, HTML, headers, URLs, and attachment metadata are sensitive user-owned data. API retrieval is filtered by the authenticated user. Password hashes are never returned by response schemas, and the application does not log database contents or secrets.
