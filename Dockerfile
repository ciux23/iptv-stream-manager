FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir aiohttp==3.12.15 pyyaml==6.0.2 curl-cffi

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY app.py .

RUN chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health', timeout=3).status == 200 else 1)"

CMD ["python", "app.py"]