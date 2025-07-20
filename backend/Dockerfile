FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including fonts
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app
COPY app/ ./app/

# Copy frontend files from parent directory
COPY ../frontend/ ./frontend/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]






