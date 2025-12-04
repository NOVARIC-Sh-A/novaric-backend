# Use a lightweight Python runtime
FROM python:3.10-slim

# Create application directory
WORKDIR /app

# Install system dependencies if needed (uncomment as required)
# RUN apt-get update && apt-get install -y build-essential

# Copy ONLY requirements first (to optimize build caching)
COPY novaric-backend/requirements.txt /app/requirements.txt

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY novaric-backend/ /app/

# Cloud Run exposes port 8080
ENV PORT=8080
EXPOSE 8080

# Start FastAPI using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
