FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including fonts and WeasyPrint dependencies
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

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app
COPY app/ ./app/

# Copy frontend files from parent directory
COPY ../frontend/ ./frontend/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]







