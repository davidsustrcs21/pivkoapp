# Base image
FROM python:3.11-slim

# Nastav pracovní adresář
WORKDIR /app

# Zkopíruj requirements a nainstaluj závislosti
COPY requirements.txt /app/
RUN apt-get update && \
    apt-get install -y fonts-dejavu-core fonts-noto-color-emoji \
    libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Zkopíruj celý backend kód
COPY . /app

# Spusť backend
CMD ["python", "main.py"]
