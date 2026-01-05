# FROM python:3.11-slim

# # Set working directory
# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ca-certificates \
#     && rm -rf /var/lib/apt/lists/*

# # Copy requirements first for Docker caching
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy all project files into /app
# COPY . .

# # Run bot
# CMD ["python", "bot.py"]


FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project structure
COPY config/ ./config/
COPY database/ ./database/
COPY utils/ ./utils/
COPY bot/ ./bot/
COPY main.py .

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the bot
CMD ["python", "main.py"]