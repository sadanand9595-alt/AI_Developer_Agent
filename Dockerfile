# AI Command Center - minimal production image.
# Uses only what's already declared in requirements.txt.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite database and vector store live here; mount a volume at
# this path for real persistence (see DEPLOYMENT.md).
RUN mkdir -p /app/data

EXPOSE 8000

# JWT_SECRET, APP_ENV, DATABASE_URL, etc. must be supplied at
# runtime (docker run -e / --env-file / orchestrator secrets) --
# nothing sensitive is baked into the image.
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
