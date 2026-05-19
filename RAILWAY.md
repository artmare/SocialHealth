# Railway deployment

Railway must run the app with a persistent Postgres database. Do not use SQLite
for production accounts.

## Required Railway variables

Set these variables on the Railway app service:

```env
FLASK_CONFIG=production
SECURE_COOKIES=true
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

`DATABASE_URL` can also be a normal external Postgres URL. The app accepts
`postgres://...` and normalizes it to `postgresql://...`.

## Database initialization

On Railway, the app auto-runs the current SQLAlchemy schema setup and seeds CBT
tasks on startup. This is controlled by:

```env
AUTO_INIT_DB=true
```

`AUTO_INIT_DB` defaults to true on Railway. Keep it enabled for the current
schema. If you later add real migrations, run migrations in the deploy workflow
and disable startup schema creation.

## GitHub Actions secrets

The deploy workflow needs these repository secrets:

```env
RAILWAY_TOKEN=...
RAILWAY_PROJECT_ID=...
RAILWAY_SERVICE_ID=...
RAILWAY_ENVIRONMENT_ID=...
```

The workflow uses Node.js 24 for the Railway CLI and `railway up --ci` so build
errors are visible directly in GitHub Actions logs.
