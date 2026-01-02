FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt .
COPY bot.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
