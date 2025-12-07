# ============================
# 1) Base builder image
# ============================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (then removed in final stage)
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

# Add non-root user
RUN useradd -m appuser
USER appuser

WORKDIR /app

# Copy installed dependencies
COPY --from=builder /root/.local /home/appuser/.local

# Export PATH for local installs
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy backend code
COPY novaric-backend/ /app/

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
