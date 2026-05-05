# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Fly uses 8080 by default)
EXPOSE 8080

# Run your app
CMD ["python", "server.py"]