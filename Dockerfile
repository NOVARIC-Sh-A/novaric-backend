# Use a lightweight and stable Python runtime
FROM python:3.10-slim

# Set application working directory
WORKDIR /app

# Copy requirements first for Docker caching
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire backend source code
COPY . /app/

# Cloud Run exposes port 8080
ENV PORT=8080
EXPOSE 8080

# Start FastAPI using uvicorn (Cloud Run compliant)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
