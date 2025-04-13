#!/bin/bash
cd "$(dirname "$0")"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install PyQt6 matplotlib numpy librosa ffmpeg-python
