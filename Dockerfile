# Use a lightweight Python runtime
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first for Docker caching
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy ALL backend files (because they are in repo root)
COPY . /app/

# Expose Cloud Run port
ENV PORT=8080
EXPOSE 8080

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
