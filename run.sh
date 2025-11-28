#!/bin/bash

# Run script for SmartReco

echo "Starting SmartReco services..."

docker-compose up -d

echo "Services started!"
echo "Frontend: http://localhost"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"







