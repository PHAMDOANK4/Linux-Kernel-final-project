FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash \
    coreutils \
    cron \
    util-linux \
    tzdata \
    procps \
    iproute2 \
    apt-utils && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x scripts/*.sh

EXPOSE 5000
CMD ["python", "app.py"]
