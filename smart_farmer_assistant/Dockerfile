# ---------------------------------------------------------------------
# Smart Farmer Assistant — production container
# Build : docker build -t smart-farmer .
# Run   : docker run -p 5000:5000 --env-file .env smart-farmer
# ---------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

WORKDIR /app

# Build dependencies for Pillow and scientific wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libjpeg-dev zlib1g-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Train the three scikit-learn models at build time so the image ships ready.
RUN python ml/train_all.py

RUN mkdir -p uploads logs && useradd -m sfa && chown -R sfa:sfa /app
USER sfa

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -fsS http://localhost:${PORT}/healthz || exit 1

CMD ["sh", "-c", "gunicorn 'app:create_app()' --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120"]
