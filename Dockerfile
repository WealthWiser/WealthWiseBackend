# Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render will map this port; we’ll still default to 8000 locally
ENV PORT=8000
EXPOSE 8000

# Use $PORT if Render sets it, otherwise 8000 locally; add a generous keep-alive
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --timeout-keep-alive 120"]
