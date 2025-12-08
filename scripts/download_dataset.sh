#!/bin/bash

# Script to download the full Bank Marketing dataset from UCI
# Original dataset: https://archive.ics.uci.edu/ml/datasets/Bank+Marketing

echo "Downloading Bank Marketing dataset..."

# Create data directory if it doesn't exist
mkdir -p data

# Download the dataset
curl -L -o data/bank-full.csv \
  "https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank-full.csv"

# Also download the smaller version
curl -L -o data/bank.csv \
  "https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank.csv"

echo "Dataset downloaded successfully!"
echo "Files:"
echo "  - data/bank-full.csv (full dataset)"
echo "  - data/bank.csv (smaller version)"








