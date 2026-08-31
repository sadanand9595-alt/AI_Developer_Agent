# Deployment

Minimal deployment path for the existing FastAPI app (`api/app.py`).
No new framework; runs with what's already in `requirements.txt`.

## Required environment variables

| Variable | Required | Notes |
|---|---|---|
| `APP_ENV` | Yes (prod) | Set to `production`. Startup refuses to boot if `JWT_SECRET` is still the default while this is anything other than `development`. |
| `JWT_SECRET` | **Yes (prod)** | Must be a real, random secret (32+ bytes recommended). Never commit it. Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `DATABASE_URL` | Recommended | Defaults to `sqlite:///./data/command_center.db`. See SQLite note below. |
| `APP_HOST` / `APP_PORT` | Optional | Default `127.0.0.1:8000`; the container CMD binds `0.0.0.0:8000` regardless. |
| `JWT_ACCESS_EXPIRES_MINUTES` | Optional | Default `30`. |
| `LOG_LEVEL` | Optional | Default `INFO`. |

All other variables in `.env.example` (AI provider keys, workspace/agent settings) are unrelated to the API layer and optional.

**Never commit `JWT_SECRET` or any `.env` file.** `.env` and `*.db` are already gitignored.

## SQLite suitability

The app uses SQLite (a single file, `data/command_center.db`). This is fine for a single-instance deployment. It is **not** suitable for multi-instance/horizontally-scaled deployments (no shared concurrent-writer database) — that would require switching `DATABASE_URL` to a networked database (e.g. Postgres), which is a config change only (SQLAlchemy already abstracts this) but is out of scope here since it wasn't requested and isn't needed for a single-instance deploy.

For persistence across container restarts, mount a volume at `/app/data`.

## Deploy with Docker

```bash
docker build -t ai-command-center .

docker run -d \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  -v ai-command-center-data:/app/data \
  --name ai-command-center \
  ai-command-center
```

## Deploy without Docker (bare metal / VM)

```bash
pip install -r requirements.txt

export APP_ENV=production
export JWT_SECRET="<your-real-secret>"

uvicorn api.app:app --host 0.0.0.0 --port 8000
```

## Verify after deploy

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Database tables and environment validation run automatically on
startup (`api/app.py` lifespan). If `JWT_SECRET` is missing/default
in a non-development `APP_ENV`, startup fails fast with a clear
error instead of running insecurely.
