FROM python:3.11-slim

# Nastavení pracovního adresáře
WORKDIR /app

# Aktualizace a instalace základních nástrojů + fontů + závislostí
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        apt-utils \
        ca-certificates \
        gnupg \
        fonts-dejavu-core \
        fonts-noto-color-emoji \
        libpango-1.0-0 \
        libharfbuzz0b \
        libpangoft2-1.0-0 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Zkopíruj requirements a nainstaluj Python balíčky
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Zkopíruj celý backend kód
COPY . /app

# Spusť backend
CMD ["python", "main.py"]
