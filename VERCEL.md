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
DATABASE_URL=postgresql://...
```

Optional:

```text
RATELIMIT_STORAGE_URI=memory://
```

`SECURE_COOKIES` defaults to `true` in production/Vercel. Set
`SECURE_COOKIES=false` only for local HTTP debugging.

## Database behavior

If `DATABASE_URL` is set, the app uses that database.

`DATABASE_URL` is required on Vercel production. Use a hosted Postgres database
such as Vercel Postgres, Neon, Supabase, Railway Postgres, or another managed
Postgres provider.

The app no longer silently uses SQLite on Vercel production because serverless
filesystems are ephemeral. Without a persistent external database, accounts,
diary entries, settings, and progress can disappear after cold starts, redeploys,
or instance replacement.

For a disposable demo only, you can explicitly opt into temporary SQLite:

```text
ALLOW_TMP_SQLITE=true
```

With `ALLOW_TMP_SQLITE=true`, the app uses SQLite in `/tmp`, runs
`db.create_all()`, and seeds CBT tasks when the task table is empty. Do not use
this mode for real users.

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
