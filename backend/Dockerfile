FROM python:3.11-slim

WORKDIR /app

# Instalace základních balíků + závislostí pro fonty
RUN apt-get update -y --fix-missing && \
    apt-get install -y --no-install-recommends \
        apt-utils \
        ca-certificates \
        fonts-dejavu-core \
        fonts-noto-color-emoji \
        libpango-1.0-0 \
        libharfbuzz0b \
        libpangoft2-1.0-0 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
        wget \
        gnupg \
        lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Zkopíruj a nainstaluj requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Zkopíruj celý kód
COPY . /app

# Spusť aplikaci
CMD ["python", "main.py"]
