#!/usr/bin/env bash
# build.sh — Render Build Script for DeepScanX-AI Backend
# This runs during Render's build phase (not at runtime).
set -e

echo "=== DeepScanX-AI Build ==="

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download model weights from Hugging Face Hub
echo "=== Downloading model weights from Hugging Face ==="
cd backend
python -c "from utils.model_downloader import download_all_models; download_all_models('.')"
cd ..

echo "=== Build complete ==="
