# PhishZero API

Base URL for local development: `http://127.0.0.1:8000`

Private endpoints use:

```http
Authorization: Bearer <access-token>
```

Tokens, passwords, raw email bodies, and attachment contents must not be logged or included in client-side error reports.

## Health

### `GET /api/health`

Returns a lightweight service check:

```json
{
  "status": "ok",
  "service": "phishguard-ai"
}
```

The `service` value is the existing internal health-contract identifier and is intentionally preserved for compatibility.

## Authentication

### `POST /api/auth/register`

Creates an account. Passwords must be 8–128 characters and contain at least one letter and one digit.

```json
{
  "email": "analyst@example.com",
  "password": "example-password-123",
  "display_name": "Analyst"
}
```

Returns a user profile without a password or password hash. Duplicate email addresses return `409`.

### `POST /api/auth/login`

Accepts the same email/password credential shape and returns a short-lived bearer token:

```json
{
  "access_token": "<access-token>",
  "token_type": "bearer"
}
```

Invalid credentials return `401` without revealing which credential was incorrect.

### `GET /api/auth/me`

Returns the authenticated user profile. Missing, invalid, expired, or unknown-user tokens return `401`.

## Email ingestion

### `POST /api/emails`

Requires authentication. Supports:

- `application/json` with `sender`, `recipients`, `subject`, `body_text`, optional `html_body`, and optional `raw_headers`.
- `multipart/form-data` containing exactly one `.eml` file.
- `message/rfc822` raw message bytes.

Uploads are limited to 5 MiB by the email parser and the application has a global request limit. Only metadata is extracted for attachments. The server never opens or executes attachments and never visits extracted URLs.

The response contains the stored email ID, parsed fields, extracted URLs, attachment metadata, and timestamps. Raw email content is returned only from this authenticated ingestion response and should be handled as sensitive data.

## Analysis

### `POST /api/analysis`

Requires authentication and accepts the structured email request:

```json
{
  "sender": "sender@example.com",
  "recipients": ["recipient@example.com"],
  "subject": "Account notice",
  "body_text": "Please review this message.",
  "html_body": null,
  "raw_headers": [
    {"name": "Authentication-Results", "value": "mx.example; spf=pass"}
  ]
}
```

The response includes `analysis_id`, `classification`, `risk_score`, `confidence`, `text_score`, `url_score`, `header_score`, `threats`, `analyzed_urls`, `model_version`, `summary`, `reasons`, `recommended_actions`, and `created_at`.

Classification values are `SAFE`, `LOW_RISK`, `SUSPICIOUS`, and `PHISHING`. `risk_score` is 0–100 and `confidence` is 0–1.

### `GET /api/analysis/{analysis_id}`

Returns one analysis only if it belongs to the authenticated user. Other users’ records are returned as `404`.

### `GET /api/analysis/history?limit=20&offset=0`

Returns the authenticated user’s analyses ordered newest first. `limit` is bounded from 1 to 100; `offset` must be non-negative.

## Validation and error behavior

- `401` — missing or invalid authentication
- `400` — malformed email or upload
- `409` — duplicate account
- `413` — request or email exceeds configured size
- `415` — unsupported content type or file type
- `422` — schema validation failure
- `429` — local rate limit exceeded
- `500` — generic internal error without stack traces or filesystem paths

All private resource queries enforce ownership through the authenticated user ID.
