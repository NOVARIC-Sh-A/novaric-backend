# ============================
# 1) Builder stage
# ============================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip --no-cache-dir \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ============================
# 2) Runtime stage
# ============================
FROM python:3.11-slim

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HOME=/home/appuser

RUN useradd -m appuser

WORKDIR /app

# Dependencies
COPY --from=builder /install /home/appuser/.local/
ENV PATH="/home/appuser/.local/bin:${PATH}"

# App source
COPY . /app

RUN mkdir -p /app/static \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

# ------------------------------------------------
# SINGLE ENTRYPOINT — ENV-DRIVEN
# ------------------------------------------------
# Cloud Run sets:
#   APP_MODULE=main:app           (novaric-backend)
#   APP_MODULE=runner_http:app    (forensic-runner)
#
CMD sh -c 'uvicorn "${APP_MODULE}" --host 0.0.0.0 --port "${PORT}"'
