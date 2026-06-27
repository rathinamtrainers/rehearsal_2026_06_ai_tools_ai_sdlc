# LearnFlow auth backend — runtime image.
# Build from the backend/ directory:  docker build -t learnflow-auth ./backend
FROM python:3.13-slim AS runtime

# Predictable, log-friendly Python.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install runtime deps first so the layer caches until requirements change.
# Only requirements.txt (not the -dev test/lint extras) ships in the image.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code + DB migrations.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Liveness probe against the app's /health endpoint.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
