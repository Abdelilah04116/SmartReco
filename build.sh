#!/bin/bash

# Build script for SmartReco

echo "Building SmartReco..."

# Build backend
echo "Building backend..."
cd backend
docker build -t smart-reco-backend .
cd ..

# Build frontend
echo "Building frontend..."
cd frontend
docker build -t smart-reco-frontend .
cd ..

echo "Build complete!"













