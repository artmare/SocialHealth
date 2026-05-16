# Vercel deployment

This project can run on Vercel through the Python serverless entrypoint in
`api/index.py`.

## Files

- `vercel.json` routes all requests to the Flask app.
- `api/index.py` creates the Flask app for Vercel and prepares a temporary
  SQLite database only when no external database is configured.
- `pyproject.toml` explicitly points Vercel at `api/index.py` so the Python
  builder does not try to auto-detect a Flask entrypoint from root files.
- `config.py` enables secure cookies in production and on Vercel.

## Environment variables

Set these in Vercel Project Settings:

```text
FLASK_CONFIG=production
SECRET_KEY=<long-random-secret>
JWT_SECRET_KEY=<long-random-secret>
ANTHROPIC_API_KEY=<your-key>
```

Recommended for real production:

```text
DATABASE_URL=postgresql://...
RATELIMIT_STORAGE_URI=memory://
```

`SECURE_COOKIES` defaults to `true` in production/Vercel. Set
`SECURE_COOKIES=false` only for local HTTP debugging.

## Database behavior

If `DATABASE_URL` is set, the app uses that database.

If `DATABASE_URL` is missing on Vercel, the app falls back to:

```text
sqlite:////tmp/socialhealth.db
```

That fallback is useful for smoke tests and demos, but `/tmp` is ephemeral in
serverless environments. Data can disappear after cold starts, redeploys, or
instance replacement. Use a hosted Postgres database for persistent accounts,
diary entries, progress, and settings.

For the `/tmp` SQLite fallback, `api/index.py` runs `db.create_all()` and seeds
the CBT task list when the task table is empty.

## Deploy

1. Push the repository to GitHub.
2. Import it in Vercel.
3. Add the environment variables above.
4. Deploy.

For local Vercel testing:

```bash
npm i -g vercel
vercel dev
```

For normal local Flask development, keep using:

```bash
pip install -r requirements-dev.txt
flask run
```
