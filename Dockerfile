# ============================
# 1) Base builder image
# ============================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from repo root (correct path)
COPY novaric-backend/requirements.txt requirements.txt

# Install dependencies to a known directory
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt



# ============================
# 2) Final runtime image
# ============================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH="/app"

# Create non-root user
RUN useradd -m appuser
USER appuser

WORKDIR /app

# Copy installed Python libraries to final image
COPY --from=builder /install /home/appuser/.local/
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy backend source code
COPY --chown=appuser:appuser novaric-backend/ /app/

# Cloud Run listens on port 8080
EXPOSE 8080

# Start FastAPI app
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}