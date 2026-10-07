FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DATA_DIR=/data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY assistant ./assistant
COPY server.py .

EXPOSE 8080

# One worker keeps SQLite writes simple; threads handle concurrent requests.
CMD exec gunicorn --workers 1 --threads 4 --bind 0.0.0.0:${PORT} --access-logfile - server:app
