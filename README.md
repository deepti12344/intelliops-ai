# IntelliOps AI — Incident Intelligence Dashboard

A local-first **full-stack portfolio MVP** for recording and triaging software incidents. Features include a responsive web dashboard, Python JSON API, SQLite persistence, explanatory severity classification, incident filtering, unit tests, and GitHub Actions CI. No packages or API keys needed.

> **Scope:** The working demo uses keyword heuristics, not a trained ML model, LLM, RAG, semantic search, or automatic root-cause diagnosis. Recommendations require human review. Use synthetic data only.

## Quick start

Requires Python 3.11+.

```bash
git clone https://github.com/deepti12344/intelliops-ai.git
cd intelliops-ai
python3 app.py
```

Open **http://127.0.0.1:8000**. For this feature branch, switch to `feature/working-incident-intelligence-mvp` after cloning if the PR has not been merged.

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

Optional environment variables: `HOST` (default `127.0.0.1`), `PORT` (default `8000`), `INTELLIOPS_DB` (default `data/incidents.sqlite3`).

## How it works

```text
Browser (web/index.html + style.css + main.js)
      | HTTP JSON fetch
      v
Python server (app.py)
      | validates data -> classifies incident -> generates explanation
      v
SQLite database (data/incidents.sqlite3)
```

1. Enter an incident title, affected service, and description.
2. Press **Analyze & save incident**.
3. The API validates the request and assigns a severity with a transparent explanation.
4. A parameterized SQL query stores the incident.
5. The dashboard reloads the incident list, totals and severity counts; filters are available. Data persists across restarts.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health |
| GET | `/api/incidents` | Latest 100 incidents |
| GET | `/api/incidents?severity=high` | Filter by severity |
| POST | `/api/incidents` | Validate, classify and persist an incident |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/incidents \
  -H 'Content-Type: application/json' \
  -d '{"title":"API timeout","description":"Payments 500 error after deployment","service":"payments-api"}'
```

The rule engine checks critical phrases first (such as `production down`), then high (such as `timeout`), then medium (such as `slow`). With no matched signals, it assigns low. These are approximate illustrative labels, not reliable safety ratings.

## Files

- `app.py` — Python HTTP API, validation, severity classifier and SQLite
- `web/index.html` — dashboard markup
- `web/style.css` — responsive styling
- `web/main.js` — API calls, form and incident rendering
- `tests/test_app.py` — validation, classification, persistence and SQL safety tests
- `.github/workflows/tests.yml` — automated tests on push and pull requests
- `.gitignore` — excludes local databases, secrets and Python caches

## Security and limitations

Local-only by default. Parameterized queries protect against SQL injection; dynamic UI content is rendered with `textContent` instead of HTML insertion. JSON request size and field lengths are limited. **This demo lacks authentication, authorization, encryption-at-rest, rate limiting, schema migrations and a production reverse proxy. Do not expose it publicly or enter sensitive operational data.**

## Interview explanation

A user enters a report in the browser, JavaScript sends POST JSON, Python validates and classifies, SQLite persists the record, then a GET request updates the dashboard. Tradeoffs: SQLite is easy for local prototyping but a production multi-instance platform would use managed PostgreSQL; transparent rules are explainable but weaker than evaluated statistical detection models.

## Next milestones

Production authentication, PostgreSQL and migrations, integration tests, incident similarity search, optional retrieval-assisted recommendations, human review, deployment and observability.
