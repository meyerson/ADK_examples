# Minimal Python container aligned to ADC-first local dev
FROM python:3.11-slim

WORKDIR /app

# System deps (optional): add build tools if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.3
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
    && poetry config virtualenvs.create false

# Copy project manifest and (optionally) lock file
COPY pyproject.toml ./

# Install dependencies (uses lock if present)
RUN poetry install --no-interaction --no-ansi

# Copy default agent into internal path; can be overridden by a volume mount

# Default command; creds and project provided at runtime
WORKDIR /app/agents
CMD ["adk", "web", "--host", "0.0.0.0"]
