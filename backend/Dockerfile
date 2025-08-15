FROM python:3.11-slim

WORKDIR /app

# Instalace závislostí systému
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-noto-color-emoji \
    libpango-1.0-0t64 \
    libharfbuzz0b0t64 \
    libpangoft2-1.0-0t64 \
    libgdk-pixbuf-2.0-0t64 \
    libffi-dev \
    shared-mime-info \
 && rm -rf /var/lib/apt/lists/*

# Instalace Python závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírování zdrojů
COPY . .

CMD ["python", "main.py"]
