# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ARG UID=1000
ARG GID=1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/ \
    ALEMBIC_CONFIG=/_app/_postgres/alembic.ini

# OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create user with same UID/GID as the host user so bind-mounted files are owned correctly
RUN groupadd -g ${GID} appuser && useradd -m -u ${UID} -g ${GID} appuser
WORKDIR /app

# (Optional) fast Python installer: uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install deps
COPY requirements.txt /app/requirements.txt
RUN uv pip install --system -r /app/requirements.txt

# App source + entrypoint (product code is bind-mounted at runtime)
COPY --chown=appuser:appuser _fastapi/ /_app/_fastapi/
COPY --chown=appuser:appuser _dramatiq/ /_app/_dramatiq/
COPY --chown=appuser:appuser _apscheduler/ /_app/_apscheduler/
COPY --chown=appuser:appuser _postgres/ /_app/_postgres/
COPY --chown=appuser:appuser _jobs/ /_app/_jobs/
COPY --chown=appuser:appuser _prometheus/ /_app/_prometheus/
COPY --chown=appuser:appuser _jsonlogger/ /_app/_jsonlogger/
COPY --chown=appuser:appuser _studio/ /_app/_studio/
COPY --chown=appuser:appuser _graphiti/ /_app/_graphiti/
COPY --chown=appuser:appuser core.py /_app/core.py
COPY --chown=appuser:appuser __init__.py /_app/__init__.py
RUN chmod +x /_app/_fastapi/entrypoint.sh
RUN chown -R appuser:appuser /app
USER appuser

# Use entrypoint script instead of default command
CMD ["/_app/_fastapi/entrypoint.sh"]
