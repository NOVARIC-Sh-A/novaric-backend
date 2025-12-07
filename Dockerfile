FROM python:3.10-slim

WORKDIR /app

# Copy requirements first
COPY ./novaric-backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL backend source files
COPY ./novaric-backend/ ./

# Cloud Run port
ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
