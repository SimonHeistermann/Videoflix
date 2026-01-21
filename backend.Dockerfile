FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        postgresql-client \
        ffmpeg \
        bash && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x backend.entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./backend.entrypoint.sh"]