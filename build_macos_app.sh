#!/bin/bash

set -e

echo "📦 Setting up virtual environment..."
python3 -m venv venv

echo "📥 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "🎨 Building VizLab macOS App with PyInstaller..."

venv/bin/pyinstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "VizLab" \
    --icon "img/icon.icns" \
    vizlab.py

echo "✅ Build complete! You can find VizLab.app in the dist/ folder."
