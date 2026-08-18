FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir aiohttp==3.12.15 pyyaml==6.0.2

COPY app.py .

CMD ["python", "app.py"]
