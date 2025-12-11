# ============================
# 1) Base builder image
# ============================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install all Python dependencies into /install
COPY requirements.txt requirements.txt

RUN pip install --prefix=/install --no-cache-dir -r requirements.txt



# ============================
# 2) Final runtime image
# ============================
FROM python:3.11-slim

# Cloud Run expects the app to listen on $PORT
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Ensures absolute imports work (e.g., "import utils.x")
ENV PYTHONPATH="/app"

# Create non-root user (Cloud Run best practice)
RUN useradd -m appuser
USER appuser

WORKDIR /app

# Add site-packages from builder stage
COPY --from=builder /install /home/appuser/.local/
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy the entire backend source code
COPY --chown=appuser:appuser . /app

# Expose the port FastAPI will run on
EXPOSE 8080

# Start application via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
