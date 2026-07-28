#!/bin/bash
# Bash script to start Docker development environment
# Usage: ./start-docker.sh

echo "Starting Aston AI Research Tool with Docker..."

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "Creating .env file from .env.example..."
    cp backend/.env.example backend/.env
    echo "Please edit backend/.env and add your API keys before continuing!"
    read -p "Press Enter to continue after editing .env file..."
fi

# Start Docker Compose
echo "Starting Docker containers..."
docker-compose up --build
