# Deploying this backend to Render

`render.yaml` in this directory declares both services. Point Render at it as a
Blueprint and it creates them together.

## What gets deployed

- The FastAPI app, from the `Dockerfile` in this directory.
- A Key Value (Redis) instance, which is the app's only datastore. Sessions,
  connected databases, and conversations all live there, and all of it expires
  within 24 hours.

There are no migrations and no application database to provision.

## Setup

1. Push the repository to GitHub.
2. In Render, **New → Blueprint**, and select the repo.
3. Set the blueprint's root directory to `backend`.
4. Fill the secrets Render prompts for: `GROQ_API_KEY`, `CREDENTIALS_KEY`, and
   `CORS_ORIGINS` (the exact origin your frontend is served from, e.g.
   `https://sql-agent-lake.vercel.app`). `SECRET_KEY` is generated for you, and
   `REDIS_URL` is wired from the Key Value service.
5. Deploy.

Generate `CREDENTIALS_KEY` with:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

## The cookie has to be cross-site

The session is a cookie, and the frontend is on a different site from the API,
so the blueprint sets `SESSION_COOKIE_SAMESITE=none` and
`SESSION_COOKIE_SECURE=true`. Both are required: browsers drop a `SameSite=None`
cookie that is not `Secure`, and `Secure` needs HTTPS, which Render terminates.

The frontend must send `credentials: 'include'` on every request, and
`CORS_ORIGINS` must list its exact origin — a wildcard is not usable with
credentials.

## What Render cannot reach

The databases people connect are their own. A Render service cannot reach a
database on someone's `localhost`; it needs one that is reachable from the
public internet, or a tunnel.
