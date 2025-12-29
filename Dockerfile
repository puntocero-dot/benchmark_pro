FROM python:3.12-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2t64 \
    libxshmfence1 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxi6 \
    libxrandr2 \
    libxfixes3 \
    libxcursor1 \
    libxdamage1 \
    libxcomposite1 \
    libpango-1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc-s1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxss1 \
    libxtst6 \
    wget \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Run the application
CMD ["python", "run.py"]
