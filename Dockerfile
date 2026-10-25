FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /rexbots
COPY requirements.txt .
RUN pip install -U pip && pip install -U -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
