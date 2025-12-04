# Use Python image
FROM python:3.10-slim

# Create working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

# Expose Cloud Run port
ENV PORT=8080
EXPOSE 8080

# Start FastAPI using uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
