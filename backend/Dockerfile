FROM python:3.11-slim-bookworm

WORKDIR /app

# Instalace závislostí systému
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-noto-color-emoji \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
 && rm -rf /var/lib/apt/lists/*

# Instalace Python závislostí
# --upgrade pip zajistí aktuální verzi pipu pro případ, že requirements potřebují novější
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Kopírování zdrojů
COPY . .

CMD ["python", "main.py"]
