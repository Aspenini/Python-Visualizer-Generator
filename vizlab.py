
import os
import platform
import sys
import numpy as np
import matplotlib.pyplot as plt
import librosa
from pathlib import Path
from datetime import datetime
import logging
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QCoreApplication, QThread, pyqtSignal

system = platform.system()
if system == "Windows":
    root = Path(os.getenv("APPDATA")) / "VizLab"
elif system == "Darwin":
    root = Path.home() / "Library" / "Application Support" / "ApeXPloit Studios" / "VizLab"
else:
    root = Path.home() / ".local" / "share" / "VizLab"

input_folder = root / "input"
output_folder = root / "output"
temp_folder = root / "temp_frames"
log_folder = root / "error_logs"

for folder in [input_folder, output_folder, temp_folder, log_folder]:
    folder.mkdir(parents=True, exist_ok=True)

log_file = log_folder / f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class Worker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_file, fps, resolution, color, amplitude_scale, point_size, video_format):
        super().__init__()
        self.audio_file = audio_file
        self.fps = fps
        self.resolution = resolution
        self.color = color
        self.amplitude_scale = amplitude_scale
        self.point_size = point_size
        self.video_format = video_format

    def run(self):
        audio_path = Path(self.audio_file)
        num_frames_generated = 0
        try:
            y, sr = librosa.load(audio_path, mono=False)
            left_channel = y[0]
            right_channel = y[1]
            left_channel /= np.max(np.abs(left_channel))
            right_channel /= np.max(np.abs(right_channel))

            frame_step = int(sr / self.fps)
            num_frames = len(left_channel) // frame_step
            width, height = self.resolution
            figsize = (width / 100, height / 100)
            color_rgb = (self.color.red() / 255, self.color.green() / 255, self.color.blue() / 255)

            for i in range(num_frames):
                start = i * frame_step
                end = min(start + frame_step, len(left_channel))
                left_chunk = left_channel[start:end]
                right_chunk = right_channel[start:end]

                amplitude = np.mean(np.abs(left_chunk) + np.abs(right_chunk)) * self.amplitude_scale
                theta = np.arctan2(right_chunk, left_chunk)
                r = np.sqrt(left_chunk**2 + right_chunk**2) * (1 + amplitude)

                fig = plt.figure(figsize=figsize, facecolor='black', dpi=200)
                ax = fig.add_subplot(111, polar=True, facecolor='black')
                ax.scatter(theta, r, s=self.point_size, c=[color_rgb], alpha=0.5, edgecolors='none')
                ax.set_ylim(0, 2)
                ax.set_yticks([])
                ax.set_xticks([])
                ax.spines['polar'].set_visible(False)
                fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

                frame_path = temp_folder / f"frame_{i:05d}.png"
                plt.savefig(frame_path, dpi=200, facecolor='black')
                print(f"[✓] Frame {i} saved to {frame_path}")
                plt.close()
                num_frames_generated += 1
        except Exception as e:
            print(f"❌ Error: {e}")
        if num_frames_generated > 0:
            print(f"✅ Done: {num_frames_generated} frames saved.")

if __name__ == '__main__':
    if len(sys.argv) >= 8:
        app = QCoreApplication(sys.argv)
        audio_file = sys.argv[1]
        fps = int(sys.argv[2])
        resolution = tuple(map(int, sys.argv[3].split("x")))
        color = QColor(sys.argv[4])
        amplitude_scale = float(sys.argv[5])
        point_size = float(sys.argv[6])
        video_format = sys.argv[7]

        worker = Worker(audio_file, fps, resolution, color, amplitude_scale, point_size, video_format)
        worker.start()
        app.exec()
