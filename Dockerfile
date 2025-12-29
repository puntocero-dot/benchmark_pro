FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app

# Install system deps if needed (usually python image has them)
RUN pip install --upgrade pip

# Copy and install requirements
COPY price_monitor_v2/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY price_monitor_v2/ price_monitor_v2/
COPY run_v2.py .

# Trigger playwright install just in case (though base image has it)
# RUN playwright install chromium

# Command
CMD ["python", "run_v2.py"]
