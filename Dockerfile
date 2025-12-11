# ============================
# 1) Base builder image
# ============================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install requirements into /install so runtime image stays clean
COPY requirements.txt requirements.txt

RUN pip install --prefix=/install --no-cache-dir -r requirements.txt



# ============================
# 2) Final runtime image
# ============================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH="/app"   

# Ensures imports like "from utils.x import y" work

RUN useradd -m appuser
USER appuser

WORKDIR /app

# Copy installed site-packages from builder
COPY --from=builder /install /home/appuser/.local/
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy entire backend project
COPY --chown=appuser:appuser . /app

# Expose FastAPI port
EXPOSE 8080

# Start FastAPI with Uvicorn (Cloud Run safe)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
