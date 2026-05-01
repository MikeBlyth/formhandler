# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port (default for bridge is 8080 or 8000, but we'll use 8082 to avoid conflict)
EXPOSE 8082

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
