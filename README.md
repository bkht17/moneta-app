# MONETA

MONETA shows how much of this month's budget is left when your money is spread across
several bank cards and cash. Upload your Kaspi Gold and Halyk card PDF statements, add the
cash you spent, and get one total with spending by category, the remaining budget and the
dates every source covers.

No bank login is needed. Statements are read once and never stored.

## Features

- **Statement import.** Kaspi Gold and Halyk card PDF statements are parsed on upload. The
  file is processed in memory and discarded; only the transactions are kept, with card and
  account numbers masked to their last four digits.
- **Common coverage date.** Every account must be covered from the first day of the month.
  The overview runs to the last date that all accounts cover, so a newer statement from one
  bank never makes the total look smaller than it is.
- **Cash that is counted on purpose.** The cash amount has no default: a blank field blocks
  the calculation, an explicit 0 is accepted. Cash spent after the common date can be
  recorded separately.
- **No silent deletions.** Re-uploading the same statement adds nothing. Rows that look like
  duplicates, and transfers that look like they moved between your own accounts, are shown
  to you to confirm. The total stays hidden until every question is answered. ATM
  withdrawals are never counted as purchases.
- **Overview.** Remaining budget, total spent, income, spending by category and by day,
  the full transaction list, and the rows after the common date kept outside the total.
- **Editable categories.** Changing a category moves money between categories; the total
  stays the same.
- **Review history** per month, and **Delete my data**, which removes the account,
  transactions and every review.

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, TanStack Query, Recharts, React Router |
| Backend | Python 3.13, Django 5.2, Django REST Framework, SimpleJWT, drf-spectacular |
| Parsing | pdfplumber |
| Database | PostgreSQL 17 (SQLite fallback for quick local runs) |
| Tooling | pytest, Vitest, black, flake8, ESLint, Docker, GitHub Actions |

## Getting started

### Requirements

- Python 3.12 or newer
- Node.js 20.19+ or 22.12+
- Docker (optional, for PostgreSQL)

### 1. Configure the environment

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev-only key | Django secret key; set a long random value outside development |
| `DEBUG` | `true` | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names |
| `DATABASE_URL` | SQLite file | e.g. `postgres://moneta:moneta@localhost:5432/moneta` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Origins allowed to call the API |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `moneta` | Used by the Docker Compose database |
| `VITE_API_URL` (frontend) | `/api` | API base URL for the built frontend |

Without `DATABASE_URL` the backend uses `backend/db.sqlite3`.

### 2. Start the database

```bash
docker compose up -d db
```

### 3. Run the backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

The API runs on http://localhost:8000. Interactive API docs: http://localhost:8000/api/docs/.

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. In development Vite proxies `/api` to the backend on port 8000.

### Run everything in Docker

```bash
docker compose up --build
```

This starts PostgreSQL and the backend; run the frontend with `npm run dev` as above.

## Demo data

Synthetic statements and a ready-made account make it easy to try the app without real
bank files:

```bash
cd backend
.venv/bin/python manage.py make_sample_statements --out samples
.venv/bin/python manage.py seed_demo
```

- `make_sample_statements` writes `kaspi_gold_sample.pdf` and `halyk_card_sample.pdf` to
  `backend/samples/`. It needs a TrueType font with Cyrillic glyphs; one is found
  automatically on macOS and most Linux systems, or pass `--font /path/to/font.ttf`.
- `seed_demo` creates `demo@moneta.test` with both sample statements already imported and
  a draft review for October 2026 waiting for the cash amount. Set the password with
  `--password`; the default is defined in `ledger/management/commands/seed_demo.py`.
  Running it again resets the demo account.

To use the Django admin, create a superuser with `.venv/bin/python manage.py createsuperuser`
and open http://localhost:8000/admin/.

## How a review works

1. **Accounts and budget.** Choose the month, the accounts you used and your monthly
   spending budget.
2. **Statements.** Upload a PDF for each account, starting on the 1st of the month. MONETA
   shows what each file covers and the common date.
3. **Cash.** Enter the cash you spent up to the common date, or 0.
4. **Check.** Answer the flagged duplicates and transfers.
5. **Overview.** See the remaining budget. Start a newer review later to extend the dates.

Remaining budget is the monthly budget minus net spending up to the common date. It is not
your bank balance.

## API

All endpoints are under `/api/` and, except register, login and refresh, require
`Authorization: Bearer <access token>`.

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register/` | Create an account (`email`, `password`, `full_name`); returns tokens |
| POST | `/auth/login/` | Get `access` and `refresh` tokens |
| POST | `/auth/refresh/` | Exchange a refresh token for a new access token |
| GET, PATCH, DELETE | `/auth/me/` | Current user; `DELETE` removes the user and all their data |
| GET, POST | `/accounts/` | List or add bank accounts (`bank`: `kaspi` or `halyk`, `label`) |
| PATCH, DELETE | `/accounts/{id}/` | Rename or remove an account |
| GET, POST | `/reviews/` | List reviews or start one (`month`, `budget_kzt`, `accounts`) |
| GET, PATCH, DELETE | `/reviews/{id}/` | A review; month, budget and accounts can change while it is a draft |
| GET | `/reviews/{id}/coverage/` | Coverage per account, common date and missing inputs |
| POST | `/reviews/{id}/statements/` | Upload a PDF (multipart: `account`, `file`, up to 10 MB) |
| POST | `/reviews/{id}/submit/` | Declare cash (`cash_kzt`, optional `later_cash_kzt`, `later_cash_until`) and calculate |
| POST | `/reviews/{id}/reopen/` | Return a review to draft to add statements or change cash |
| GET | `/reviews/{id}/flags/` | Open questions about duplicates and transfers |
| POST | `/flags/{id}/resolve/` | Answer a flag: `keep_both`, `same_purchase`, `own_transfer` or `not_own_transfer` |
| GET | `/reviews/{id}/overview/` | Totals, categories, daily spending, transactions; `409` until the review is complete |
| PATCH | `/transactions/{id}/` | Change a transaction's `category` |
| GET | `/categories/` | Available categories |

Validation errors use one shape, with stable codes the frontend can rely on:

```json
{ "errors": [{ "code": "cash_missing", "message": "Enter the cash you spent, or 0 if you spent none. A blank field can't be counted." }] }
```

The OpenAPI schema is served at `/api/schema/`.

## Supported statements

| Bank | Statement | Notes |
|---|---|---|
| Kaspi | Kaspi Gold statement (PDF, Russian) | Card ending read from the header |
| Halyk | Card account statement (PDF, Russian) | Tenge accounts only; wrapped descriptions are joined |

Other files are rejected with a message that says what to upload instead. The parsers live
in `backend/ledger/parsers/`. To support a new layout, add a module with `matches(text)` and
`parse(lines)` and register it in `parsers/__init__.py`.

## Testing and code quality

```bash
cd backend
.venv/bin/black --check .
.venv/bin/flake8 .
.venv/bin/pytest -q
```

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

The backend tests run a full reference month through the API: imports, coverage, cash
validation, duplicate and transfer questions, category changes, the overview totals and
data deletion. CI runs all of the above on every push and pull request, with the backend
tests on PostgreSQL.

## Project structure

```
backend/
  moneta_backend/        settings and URL configuration
  users/                 email login, registration, account deletion
  ledger/
    models.py            accounts, reviews, statement imports, transactions, flags
    parsers/             in-memory PDF reading and the Kaspi and Halyk parsers
    services/
      intake.py          coverage, common date and input validation
      ingest.py          storing statements without duplicating rows
      reconcile.py       duplicate and transfer questions and their answers
      overview.py        totals, categories and rows outside the period
      categories.py      default category rules
    management/commands/ make_sample_statements, seed_demo
    tests/
frontend/
  src/
    components/          layout, cards, charts, shared UI
    pages/               overview, history, settings, sign-in
    pages/review/        the review steps
    lib/                 API client, queries, types, formatting
docker-compose.yml       PostgreSQL and backend for development
.github/workflows/ci.yml lint, type checks, tests and build
```

## Deployment notes

- The backend image (`backend/Dockerfile`) runs Gunicorn and serves static files with
  WhiteNoise. Set `SECRET_KEY`, `DEBUG=false`, `ALLOWED_HOSTS`, `DATABASE_URL` and
  `CORS_ALLOWED_ORIGINS`, then run `python manage.py migrate` on release.
- The frontend builds to static files with `npm run build` (`frontend/dist`). Serve them
  from any static host and either proxy `/api` to the backend or build with `VITE_API_URL`
  pointing at it.
- Keep request timeouts above 60 seconds on any proxy in front of the API, so large
  statements have time to process.

## Known limitations

- Only Kaspi Gold and Halyk card statements in tenge are supported.
- The parsers are tuned on synthetic statements. Bank layouts change, so check them
  against real statements with personal details removed before relying on the totals.
- There is no live bank connection; each review needs fresh statements.
- The frontend bundle is not code-split yet.
