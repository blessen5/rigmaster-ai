# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port (Railway sets $PORT dynamically)
EXPOSE 8080

# Run the application with Gunicorn using Railway's dynamic PORT
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120 app:app
