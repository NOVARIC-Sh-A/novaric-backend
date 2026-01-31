# ============================
# 1) Builder stage
# ============================
FROM python:3.11-slim AS builder

WORKDIR /build

# Build deps (keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install into a relocatable prefix
RUN python -m pip install --upgrade pip --no-cache-dir --disable-pip-version-check \
    && python -m pip install --prefix=/install --no-cache-dir -r requirements.txt


# ============================
# 2) Runtime stage
# ============================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080 \
    HOME=/home/appuser \
    PATH=/home/appuser/.local/bin:$PATH \
    APP_MODULE=runner_http:app

# Create non-root user
RUN useradd -m -u 10001 appuser

WORKDIR /app

# Bring dependencies from builder
COPY --from=builder /install /home/appuser/.local

# Copy application source
COPY . /app

# Ensure expected dirs + permissions
RUN mkdir -p /app/static \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

# Use sh -c so APP_MODULE and PORT env vars are honored at runtime
CMD ["sh", "-c", "python -m uvicorn ${APP_MODULE} --host 0.0.0.0 --port ${PORT}"]
