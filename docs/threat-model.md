# PhishZero Threat Model

## Scope and assumptions

This model covers the local PhishZero application as implemented through all 14 steps: the React frontend, FastAPI backend, SQLite database, passive email parser, static URL analyzer, email-header analyzer, risk engine, explainability engine, and local ML training/prediction components.

The system is defensive cybersecurity research software. It analyzes untrusted email content as data. It does not send email, visit extracted URLs, crawl websites, execute attachments, execute JavaScript from email HTML, or actively scan external infrastructure.

The deployment is assumed to run behind a trusted local or authorized network boundary. Production deployment still requires TLS, protected infrastructure, operational monitoring, and a production-grade distributed rate limiter.

## Assets

| Asset | Security property | Location / owner |
| --- | --- | --- |
| User credentials | Passwords must not be recoverable or exposed | Argon2 hash in SQLite `users.password_hash` |
| JWT signing secret | Confidentiality and integrity | Environment variable only |
| Access tokens | Confidentiality, integrity, expiration | Browser session and Authorization headers |
| Email body and HTML | Confidentiality and safe handling | Authenticated user-owned email records |
| Raw email headers | Confidentiality and integrity | Authenticated user-owned email records |
| Attachment metadata | Confidentiality and safe handling | Authenticated user-owned email records |
| Extracted URLs and threat indicators | Integrity and confidentiality | Authenticated analysis records |
| Risk scores and explanations | Integrity and confidentiality | Authenticated analysis records |
| ML artifacts and datasets | Integrity and provenance | Local filesystem, explicitly supplied for training |
| Database relationships | Integrity and authorization boundaries | SQLite foreign keys and ownership queries |
| Application logs | Confidentiality and operational usefulness | Uvicorn/application runtime |

## Trust boundaries

1. **Browser to API boundary** — The React client sends credentials, email fields, raw headers, and optional `.eml` files to the authorized local API. Client validation is advisory; the backend validates independently.
2. **Unauthenticated to authenticated boundary** — Registration and login issue a bearer token. Private email and analysis endpoints resolve the token to a database user.
3. **User to user data boundary** — Analysis retrieval and history queries join through the owning email and current user ID. A user must not receive another user’s analysis.
4. **Untrusted email content boundary** — Message bodies, HTML, headers, attachment names, and URLs are attacker-controlled input. They are parsed or displayed as data only.
5. **Application to filesystem boundary** — ML artifacts and the SQLite database are local resources. Uploaded attachments are not written to disk or executed.
6. **Application to network boundary** — URL analysis is string-only. No analyzer or parser is permitted to make outbound requests to submitted URLs.
7. **Configuration boundary** — JWT secret, allowed frontend origins, request limits, and rate limits come from environment configuration; secrets are not source-controlled.

## Attack surfaces and mitigations

### Authentication and JWT handling

**Threats:** password guessing, weak password storage, token forgery, algorithm confusion, missing/expired tokens, secret leakage, and session theft through browser script injection.

**Mitigations:**

- Pydantic validates email and password shape server-side.
- Passwords are stored with `pwdlib`’s recommended Argon2 configuration, never plaintext.
- JWT signing requires a runtime-provided secret of at least 32 characters.
- JWT algorithms are restricted to HS256, HS384, or HS512; the configured algorithm is explicitly passed during decode.
- Tokens require `sub` and `exp` claims and are short-lived by configuration.
- Invalid, missing, expired, malformed, and unknown-user tokens return 401 without token details.
- Authentication endpoints are process-locally rate-limited.
- Passwords and tokens are not logged by application code.

**Residual risks:** Access tokens are held in browser storage by the existing frontend, so a future XSS vulnerability could expose an active token. There is no token revocation or refresh-token rotation. Production deployments should prefer secure, HttpOnly, SameSite cookies with CSRF protection or a carefully designed short-lived in-memory token strategy.

### Authorization and data isolation

**Threats:** IDOR, history leakage, unauthorized ingestion, and cross-user analysis access.

**Mitigations:**

- `/api/emails`, `/api/analysis`, `/api/analysis/{id}`, and `/api/analysis/history` require the current-user dependency.
- Retrieval and history queries constrain records through `Email.user_id == current_user.id`.
- Foreign keys and cascades maintain ownership relationships.
- Password hashes and email bodies are not included in analysis response schemas.

**Residual risks:** Future endpoints must repeat the ownership predicate. Centralized authorization helpers or policy tests should be extended whenever new resources are added.

### CORS and browser boundaries

**Threats:** credentialed cross-origin requests from an attacker-controlled origin.

**Mitigations:**

- CORS allows explicit configured origins only.
- Wildcard origins are rejected when credentials are enabled.
- Allowed methods and headers are narrow (`GET`, `POST`, `OPTIONS`, `Authorization`, and `Content-Type`).

**Residual risks:** CORS is not an authentication control. It does not protect a stolen bearer token or replace TLS.

### Input validation and request limits

**Threats:** oversized bodies, malformed JSON, header injection, invalid addresses, oversized URLs, denial of service, and persistence errors caused by unbounded fields.

**Mitigations:**

- Pydantic schemas reject unknown fields, validate email addresses, cap text/header/recipient sizes, and reject header line breaks.
- A global middleware rejects request bodies over the configured 6 MiB default before route processing.
- The email parser independently enforces a 5 MiB message limit.
- `.eml` uploads require a normalized `.eml` filename and an allowed content type.
- URL parsing accepts only HTTP(S) URLs with a hostname and rejects whitespace/control characters.
- Rate limiting applies to authentication, ingestion, and analysis POST routes.

**Residual risks:** The process-local limiter does not coordinate across multiple workers or hosts. A production deployment should use a shared store or gateway limiter. The existing database URL column is shorter than the analyzer’s historical 8192-character URL bound; future schema/input contracts should keep those limits aligned.

### SQL and database security

**Threats:** SQL injection, unauthorized joins, orphaned records, and inconsistent foreign-key behavior in SQLite.

**Mitigations:**

- SQLAlchemy expressions and bound parameters are used instead of string-built SQL for application queries.
- Ownership predicates are part of retrieval queries.
- SQLite foreign-key enforcement is enabled on application connections.
- Database constraints, indexes, unique keys, and cascades are defined in the model/migration layer.

**Residual risks:** SQLite is appropriate for local research but is not the preferred concurrent production database. Database file permissions and backups remain deployment responsibilities.

### XSS and untrusted email content

**Threats:** stored or reflected XSS through email HTML, headers, URLs, threat descriptions, or model explanations.

**Mitigations:**

- The frontend renders values through React text interpolation, not `dangerouslySetInnerHTML` or `innerHTML`.
- Email HTML is never rendered as active markup in the dashboard.
- The `.eml` parser extracts text and metadata without executing scripts.
- Extracted URLs are rendered as text, not automatically visited links.
- Backend HTML/script content is passed to analysis as data only.

**Residual risks:** Any future feature that previews email HTML must use a strict sanitizer and isolated sandbox. React escaping does not protect code introduced through unsafe future DOM APIs or third-party libraries.

### File uploads and EML parsing

**Threats:** attachment execution, parser abuse, path traversal through filenames, malformed MIME structures, oversized multipart requests, and content-type spoofing.

**Mitigations:**

- Only `.eml` filenames are accepted for multipart uploads after Windows/POSIX basename normalization.
- Uploads are size-limited and parsed in memory.
- Attachment contents are never written to disk, opened as files, executed, or passed to another process.
- Attachment metadata is limited and includes filename, content type, disposition, and measured size only.
- Malformed messages return controlled client errors without stack traces.
- The parser only extracts HTTP(S) URL strings and never makes network requests.

**Residual risks:** MIME parsing is still a complex input operation. Keep parser/library versions maintained, preserve the size limits, and consider running parsing in a constrained worker for hostile production-scale traffic.

### URL analysis

**Threats:** SSRF, DNS interaction, active scanning, credential submission, URL parser confusion, and resource exhaustion.

**Mitigations:**

- Static feature extraction uses only the supplied string and `urlsplit`/IP parsing.
- No HTTP client, DNS resolver, crawler, browser, credential submission, or downloaded-content execution is used by the URL analyzer.
- URLs with unsupported schemes, missing hosts, whitespace, control characters, or malformed values are rejected.

**Residual risks:** Static URL analysis cannot prove that a destination is safe and can be evaded by attackers. It must remain strictly passive.

### Error handling and logging

**Threats:** stack-trace disclosure, filesystem path leakage, password/token logging, and sensitive request-body logging.

**Mitigations:**

- A generic application exception handler returns only `An internal server error occurred.` with no traceback or input.
- The generic exception handler logs only the request path and exception type; it does not log exception messages or tracebacks.
- Risk-engine component failures use diagnostic-safe messages without exception paths or raw input.
- Application code does not log request bodies, passwords, JWTs, or email content.
- Authentication errors use a generic invalid-credentials response.
- Error responses use `Cache-Control: no-store` for generic server and throttling errors.

**Residual risks:** Uvicorn or infrastructure access/error logs must be access-controlled and configured not to capture Authorization headers or request bodies. Operational log retention is outside this repository.

### Secret management and sensitive data exposure

**Threats:** committed secrets, verbose environment output, password/hash exposure, and API token leakage.

**Mitigations:**

- `.env` files, databases, virtual environments, caches, and ML artifacts are ignored by Git rules; `.env.example` contains placeholders only.
- JWT settings fail validation without a sufficiently long secret and an approved algorithm.
- Response models omit password hashes and raw email data from analysis results.
- No secrets are printed by application code or included in the threat model.

**Residual risks:** The frontend currently stores a bearer token in browser storage, and local SQLite contains sensitive analyzed email data. Use TLS, restrictive filesystem permissions, secure backups, and a production session strategy before deployment beyond authorized local research.

## Security test coverage

Security-focused tests are in `backend/tests/test_security_hardening.py` and cover:

- JWT algorithm allowlisting
- wildcard CORS rejection
- rate-limiter enforcement
- SQLite foreign-key enforcement
- diagnostic path/input redaction
- generic 500 responses
- global oversized-request rejection

Existing tests additionally cover password hashing/authentication failures, ownership isolation, malformed email handling, attachment metadata-only handling, URL string-only analysis, and missing ML models.

## Residual-risk priorities

1. Move bearer-token handling to a hardened production session design.
2. Use a shared rate limiter and a production database for multi-worker deployment.
3. Keep Python/Node/MIME/ML dependencies patched and review model artifacts for provenance.
4. Add structured security logging and monitoring that excludes secrets and message bodies.
5. Preserve the rule that email HTML, attachments, and extracted URLs are never executed or automatically visited.

## Final integration verification

The final release review verified the local application without scanning or contacting external systems:

- Backend test suite: 72 passed, including 9 focused security tests.
- Frontend test suite: 7 passed.
- Frontend production build: passed.
- Alembic migration consistency: passed.
- Backend startup, health endpoint, and explicit-origin CORS preflight: passed.
- Docker was not built because no Docker files are present and Docker was unavailable in the verification environment.
