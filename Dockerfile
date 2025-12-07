# ============================
# 1) Base builder image
# ============================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Correct: requirements.txt is in current backend folder
COPY requirements.txt requirements.txt

RUN pip install --prefix=/install --no-cache-dir -r requirements.txt



# ============================
# 2) Final runtime image
# ============================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH="/app"

RUN useradd -m appuser
USER appuser

WORKDIR /app

COPY --from=builder /install /home/appuser/.local/
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Correct: copy entire backend into /app
COPY --chown=appuser:appuser . /app

EXPOSE 8080

CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
