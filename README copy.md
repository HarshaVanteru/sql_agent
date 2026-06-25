# Auth Module

A plug-and-play authentication and authorization library for FastAPI applications.

30 independent modules — pick only what you need, drop it into your project, and it works.

---

## What's included

| Category | Modules |
|---|---|
| Core auth | `signup` `signin` `mfa_login_step` `signout` `signout_all` |
| Email & OTP | `verify_email` `resend_verification` `send_email_otp` `verify_email_otp` |
| Password | `change_password` `forgot_password` `reset_password` |
| MFA | `setup_totp` `verify_totp_setup` `disable_mfa` `view_backup_codes` `regenerate_backup_codes` |
| Sessions | `list_sessions` `refresh_token` |
| RBAC | `list_roles` `create_role` `assign_role` `revoke_role` `list_user_permissions` |
| Admin | `list_tenants` `create_tenant` `list_users` |
| OAuth | `signin_google` `signin_auth0` |
| Utilities | `token_health_check` |

---

## Option A — Use a single module in your existing project

Each module folder is fully self-contained. It has its own models, config, database setup, and all utilities bundled inside. No other files from this repo are needed.

### Step 1 — Copy the module folder

```bash
# Example: you only need sign-in
cp -r auth-module/packages/modules/signin  ./signin
```

Your project now looks like:
```
your-project/
  signin/
    __init__.py
    _core.py        ← all utilities (tokens, db, redis, etc.)
    models.py       ← SQLAlchemy ORM models
    schemas.py      ← Pydantic request/response schemas
    service.py      ← business logic
    router.py       ← FastAPI router
    requirements.txt
    .env.example
  main.py
```

### Step 2 — Install dependencies

```bash
pip install -r signin/requirements.txt
```

### Step 3 — Set environment variables

```bash
cp signin/.env.example .env
```

Fill in `.env` — at minimum:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/yourdb
REDIS_URL=redis://localhost:6379/0
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
SECRET_KEY=any-random-string-32-chars-minimum
```

Generate RSA keys:
```bash
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
```

### Step 4 — Wire the router into your FastAPI app

```python
# main.py
from fastapi import FastAPI
from signin import router as signin_router

app = FastAPI()
app.include_router(signin_router)
```

### Step 5 — Create the database tables

```python
# run once, in a migration script or startup hook
from signin.models import Base
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql+asyncpg://...")
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

Or use Alembic pointing at `signin/models.py`.

### Step 6 — Run

```bash
uvicorn main:app --reload
# Open http://localhost:8000/docs
```

---

## Using multiple modules together

Each module shares the same database schema (all models are identical copies). When using more than one module, run `create_all` from any one of them — they all produce the same tables.

```python
from fastapi import FastAPI
from signup import router as signup_router
from signin import router as signin_router
from verify_email import router as verify_email_router
from forgot_password import router as forgot_password_router

app = FastAPI()
app.include_router(signup_router)
app.include_router(signin_router)
app.include_router(verify_email_router)
app.include_router(forgot_password_router)
```

### Module dependency map

Some modules need data created by others. Follow this order when combining them:

```
signup
  └── verify_email          needs token from signup verification email
  └── resend_verification   needs an unverified user

signin                      needs a verified user (from above)
  ├── signout
  ├── signout_all
  ├── list_sessions
  ├── refresh_token
  ├── change_password
  ├── send_email_otp → verify_email_otp
  ├── list_user_permissions
  └── setup_totp
        └── verify_totp_setup
              ├── disable_mfa
              ├── view_backup_codes
              └── regenerate_backup_codes

forgot_password             only needs the user to exist, no login required
  └── reset_password        needs the reset token from the email

list_roles / create_role / assign_role / revoke_role   need an admin token
list_tenants / create_tenant / list_users              need an admin token

signin_google               independent — needs Google OAuth credentials in .env
signin_auth0                independent — needs Auth0 credentials in .env
token_health_check          fully independent — no DB or Redis needed
```

---

## Option B — Run the full service

The full service wires all 30 modules together behind a single FastAPI app with Docker.

```bash
cd auth-module

# 1. Copy and fill environment variables
cp .env.example .env

# 2. Start everything
docker-compose up -d

# 3. Apply database migrations
docker-compose exec auth-api alembic upgrade head

# 4. Seed default tenant, roles, and admin user
docker-compose exec auth-api python -m scripts.seed
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| MailHog (catches all emails) | http://localhost:8025 |
| PostgreSQL | localhost:5434 |
| Redis | localhost:6379 |

---

## Environment variables

### Required (all modules)

| Variable | How to generate |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `JWT_PRIVATE_KEY` | `openssl genrsa 2048` → paste PEM with `\n` |
| `JWT_PUBLIC_KEY` | `openssl rsa -pubout` → paste PEM with `\n` |
| `SECRET_KEY` | `openssl rand -hex 32` |

### Optional

| Variable | Default | Purpose |
|---|---|---|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | JWT lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |
| `MFA_ISSUER` | `AuthModule` | Label shown in authenticator apps |
| `SMTP_HOST` | `localhost` | Email server |
| `SMTP_PORT` | `1025` | Email port (1025 = MailHog) |
| `SMTP_FROM` | `noreply@auth.local` | From address on emails |
| `SMTP_USE_TLS` | `false` | Set `true` in production |
| `GOOGLE_CLIENT_ID` | — | Required for `signin_google` |
| `GOOGLE_CLIENT_SECRET` | — | Required for `signin_google` |
| `AUTH0_DOMAIN` | — | Required for `signin_auth0` |
| `AUTH0_CLIENT_ID` | — | Required for `signin_auth0` |
| `AUTH0_CLIENT_SECRET` | — | Required for `signin_auth0` |
| `RATE_LIMIT_ENABLED` | `true` | Set `false` for local testing |
| `HIBP_CHECK_ENABLED` | `true` | Check passwords against data breaches |
| `HIBP_API_KEY` | — | Optional — increases HIBP rate limits |

---

## API overview

All endpoints are prefixed with `/auth`. Protected endpoints require:
```
Authorization: Bearer <access_token>
```

| Method | Path | Module | Auth |
|---|---|---|---|
| POST | `/auth/signup` | signup | — |
| POST | `/auth/login` | signin | — |
| POST | `/auth/login/mfa` | mfa_login_step | — |
| POST | `/auth/logout` | signout | Bearer |
| POST | `/auth/logout/all` | signout_all | Bearer |
| POST | `/auth/email/verify` | verify_email | — |
| POST | `/auth/email/resend-verification` | resend_verification | — |
| POST | `/auth/otp/send` | send_email_otp | Bearer |
| POST | `/auth/otp/verify` | verify_email_otp | Bearer |
| POST | `/auth/password/change` | change_password | Bearer |
| POST | `/auth/password/forgot` | forgot_password | — |
| POST | `/auth/password/reset` | reset_password | — |
| POST | `/auth/mfa/totp/setup` | setup_totp | Bearer |
| POST | `/auth/mfa/totp/verify-setup` | verify_totp_setup | Bearer |
| POST | `/auth/mfa/disable` | disable_mfa | Bearer |
| GET | `/auth/mfa/backup-codes` | view_backup_codes | Bearer |
| POST | `/auth/mfa/backup-codes/regenerate` | regenerate_backup_codes | Bearer |
| GET | `/auth/sessions` | list_sessions | Bearer |
| POST | `/auth/token/refresh` | refresh_token | — |
| GET | `/auth/roles` | list_roles | Bearer |
| POST | `/auth/roles` | create_role | Bearer |
| POST | `/auth/users/{id}/roles` | assign_role | Bearer |
| DELETE | `/auth/users/{id}/roles/{name}` | revoke_role | Bearer |
| GET | `/auth/users/{id}/permissions` | list_user_permissions | Bearer |
| GET | `/auth/tenants` | list_tenants | Bearer |
| POST | `/auth/tenants` | create_tenant | Bearer |
| GET | `/auth/users` | list_users | Bearer |
| GET | `/auth/oauth/google/authorize` | signin_google | — |
| GET | `/auth/oauth/google/callback` | signin_google | — |
| GET | `/auth/oauth/auth0/authorize` | signin_auth0 | — |
| GET | `/auth/oauth/auth0/callback` | signin_auth0 | — |
| GET | `/auth/token/health` | token_health_check | — |

---

## Running tests

```bash
cd auth-module

# Verify all 30 modules import cleanly (no DB needed)
python scripts/check_imports.py

# Run a single module on its own Swagger UI
python scripts/run_module.py signin          # → http://localhost:8001/docs
python scripts/run_module.py signup 8002     # → http://localhost:8002/docs

# Full test suite (needs PostgreSQL)
pip install pytest pytest-asyncio httpx cryptography
pytest tests/ -v

# Unit tests only (no DB)
pytest tests/unit/ -v
```

---

## Tech stack

FastAPI · PostgreSQL · Redis · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · RS256 JWT · bcrypt · pyotp · httpx · aiosmtplib

---

## Production checklist

- [ ] Set `ENVIRONMENT=production` (disables Swagger UI)
- [ ] Use a 4096-bit RSA key pair
- [ ] Set `SECRET_KEY` to 64+ random hex bytes (`openssl rand -hex 64`)
- [ ] Point `SMTP_*` to a real mail provider (SendGrid, SES, Mailgun)
- [ ] Set `CORS_ORIGINS` to your exact frontend domain
- [ ] Set `RATE_LIMIT_ENABLED=true` and `HIBP_CHECK_ENABLED=true`
- [ ] Run behind HTTPS (nginx / load balancer with TLS)
- [ ] Set `DB_POOL_SIZE` based on expected traffic

---

## License

MIT
