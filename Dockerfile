FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    WEB_WORKERS=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-web.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-web.txt

COPY VERSION ./VERSION
COPY minimalize_engine ./minimalize_engine
COPY web ./web

RUN useradd --create-home --uid 10001 minimalizer \
    && chown -R minimalizer:minimalizer /app
USER minimalizer

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8000') + '/health', timeout=3).read()" || exit 1

CMD ["sh", "-c", "python -m uvicorn web.app:app --host 0.0.0.0 --port ${PORT} --workers ${WEB_WORKERS}"]
