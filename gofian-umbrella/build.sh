#!/usr/bin/env bash
# GOFIAN Umbrella or Sunglasses — Render Build Script
set -o errexit

echo ">> [1/4] Installing Python dependencies..."
pip install -r requirements.txt

echo ">> [2/4] Building React frontend..."
cd frontend
npm install
npm run build
cd ..

echo ">> [3/4] Initializing database..."
python migrate.py

echo ">> [4/4] Seeding demo data..."
python seed.py

echo ">> Build complete!"
