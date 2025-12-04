FROM python:3.11-slim

WORKDIR /app

COPY novaric-backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY novaric-backend/ .

ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
