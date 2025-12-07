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

COPY novaric-backend/requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt


# ============================
# 2) Final runtime image
# ============================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Create non-root user
RUN useradd -m appuser
USER appuser

# Working directory for the application
WORKDIR /app

# Copy installed dependencies
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy backend code to /app
COPY novaric-backend/ /app/

# Confirm main.py is available
# (this is where Uvicorn will look: /app/main.py)

EXPOSE 8080

# Uvicorn start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
