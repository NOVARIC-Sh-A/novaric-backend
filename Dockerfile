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

RUN python -m pip install --upgrade pip --no-cache-dir --disable-pip-version-check \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ============================
# 2) Runtime stage
# ============================
FROM python:3.11-slim

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HOME=/home/appuser

# Default module (override per service in Cloud Run env vars)
ENV APP_MODULE=main:app

RUN useradd -m appuser

WORKDIR /app

# Install deps into appuser-local bin/site-packages
COPY --from=builder /install /home/appuser/.local/
ENV PATH="/home/appuser/.local/bin:${PATH}"

# App source
COPY . /app

# Ensure static exists + permissions
RUN mkdir -p /app/static \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

# Single entrypoint — uses Cloud Run's $PORT and your APP_MODULE
CMD ["sh", "-c", "python3 -m uvicorn ${APP_MODULE} --host 0.0.0.0 --port ${PORT}"]
