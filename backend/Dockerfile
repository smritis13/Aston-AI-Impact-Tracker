# Use Python 3.9 (or any other version) as the base image
FROM python:3.9-slim

# Install system dependencies (e.g., for mysqlclient and building Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install required libraries for Playwright (Chromium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    libxss1 \
    libxcb-dri3-0 \
    libxcb-dri2-0 \
    libxcb-glx0 \
    libxcb-render0 \
    libxcb-shm0 \
    libxcb1 \
    libx11-6 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcups2 \
    libxdamage1 \
    libxfixes3 \
    && rm -rf /var/lib/apt/lists/*

# Environment variables to disable .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copy requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright and its browsers
RUN pip install playwright
RUN playwright install
# RUN pip install gunicorn


# Copy the rest of the backend code into the container
COPY . /app/

# Expose port 8000 for Django
EXPOSE 8000

# Default command to run the Django dev server
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
