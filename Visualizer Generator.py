import librosa
import numpy as np
import matplotlib.pyplot as plt
import ffmpeg
import os
import logging
from datetime import datetime
import shutil
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                            QLabel, QFileDialog, QComboBox, QProgressBar, QColorDialog, QSlider)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QFont
import sys

# Define folders relative to script location
script_dir = os.path.dirname(os.path.abspath(__file__))
input_folder = os.path.join(script_dir, "input")
output_folder = os.path.join(script_dir, "output")
log_folder = os.path.join(script_dir, "error_logs")
temp_folder = os.path.join(script_dir, "temp_frames")

# Create folders if they don’t exist
for folder in [input_folder, output_folder, log_folder, temp_folder]:
    os.makedirs(folder, exist_ok=True)

# Set up logging
log_file = os.path.join(log_folder, f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class Worker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_file, fps, resolution, color, amplitude_scale, point_size):
        super().__init__()
        self.audio_file = audio_file
        self.fps = fps
        self.resolution = resolution
        self.color = color
        self.amplitude_scale = amplitude_scale
        self.point_size = point_size

    def compile_video(self, audio_path, output_video, num_frames_generated):
        try:
            video_stream = ffmpeg.input(os.path.join(temp_folder, 'frame_%05d.png'), pattern_type='sequence', framerate=self.fps)
            audio_stream = ffmpeg.input(audio_path).audio
            video_stream = video_stream.filter('scale', self.resolution[0], self.resolution[1], force_original_aspect_ratio='decrease')
            video_stream = video_stream.filter('pad', self.resolution[0], self.resolution[1], '(ow-iw)/2', '(oh-ih)/2')
            duration = num_frames_generated / self.fps
            stream = ffmpeg.output(
                video_stream, audio_stream,
                output_video,
                vcodec='libx264',
                acodec='libmp3lame',
                audio_bitrate='192k',
                pix_fmt='yuv420p',
                r=self.fps,
                t=duration
            )
            ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
            return True
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else "No stderr output available"
            logging.error(f"Video compilation failed for {self.audio_file}: {error_msg}")
            return False

    def run(self):
        audio_path = os.path.join(input_folder, self.audio_file)
        output_video = os.path.join(output_folder, f"{os.path.splitext(self.audio_file)[0]}_gonio.mp4")
        num_frames_generated = 0

        try:
            y, sr = librosa.load(audio_path, mono=False)
            left_channel = y[0]
            right_channel = y[1]

            left_channel = left_channel / np.max(np.abs(left_channel))
            right_channel = right_channel / np.max(np.abs(right_channel))

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

                fig = plt.figure(figsize=figsize, facecolor='black')
                ax = fig.add_subplot(111, polar=True, facecolor='black')
                ax.scatter(theta, r, s=self.point_size, c=[color_rgb], alpha=0.3, edgecolors='none')
                ax.set_ylim(0, 2)
                ax.set_yticks([])
                ax.set_xticks([])
                ax.spines['polar'].set_visible(False)
                plt.title(f"{self.audio_file} - {i/self.fps:.2f}s", color='white', fontsize=24, pad=40)

                plt.savefig(os.path.join(temp_folder, f"frame_{i:05d}.png"), dpi=100, facecolor='black')
                plt.close()

                num_frames_generated += 1
                self.progress.emit(int((i + 1) / num_frames * 100))

            # Compile video after frame generation
            if num_frames_generated > 0 and os.path.exists(audio_path):
                success = self.compile_video(audio_path, output_video, num_frames_generated)
                if not success:
                    self.error.emit(f"Video compilation failed for {self.audio_file}. Check log.")

        except Exception as e:
            logging.error(f"Frame generation failed for {self.audio_file}: {str(e)}")
            self.error.emit(f"Error processing {self.audio_file}. Check log.")
            # Attempt partial video compilation
            if num_frames_generated > 0 and os.path.exists(audio_path):
                success = self.compile_video(audio_path, output_video, num_frames_generated)
                if not success:
                    self.error.emit(f"Video compilation failed for {self.audio_file}. Check log.")

        # Always clean up temp frames
        for file in os.listdir(temp_folder):
            if file.endswith('.png'):
                os.remove(os.path.join(temp_folder, file))
        if os.path.exists(audio_path):
            os.remove(audio_path)

        if num_frames_generated > 0:
            self.finished.emit(f"Processed {self.audio_file} with {num_frames_generated} frames.")
        else:
            self.error.emit(f"No frames generated for {self.audio_file}.")

class GonioVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Gonio Visualizer')
        self.setFixedSize(600, 800)
        self.audio_file = None
        self.color = QColor(0, 255, 0)
        self.amplitude_scale = 2.0
        self.point_size = 10
        self.clear_temp_frames()  # Clear temp frames on boot
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.label = QLabel("Drop or Select an Audio File")
        self.label.setFont(QFont("Arial", 14))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        select_btn = QPushButton("Select File")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a; border-radius: 15px; padding: 10px;
                font-size: 12px; color: #ffffff;
            }
            QPushButton:hover { background-color: #4a4a4a; }
        """)
        select_btn.clicked.connect(self.select_file)
        layout.addWidget(select_btn)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30 FPS", "60 FPS", "120 FPS"])
        self.fps_combo.setStyleSheet("QComboBox { background-color: #3a3a3a; border-radius: 10px; padding: 5px; }")
        layout.addWidget(self.fps_combo)

        self.res_combo = QComboBox()
        self.res_combo.addItems(["720p (1280x720)", "1080p (1920x1080)", "4K (3840x2160)"])
        self.res_combo.setStyleSheet("QComboBox { background-color: #3a3a3a; border-radius: 10px; padding: 5px; }")
        layout.addWidget(self.res_combo)

        self.color_btn = QPushButton("Choose Color")
        self.color_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a; border-radius: 15px; padding: 10px;
                font-size: 12px; color: #ffffff;
            }
            QPushButton:hover { background-color: #4a4a4a; }
        """)
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)

        self.amplitude_slider = QSlider(Qt.Orientation.Horizontal)
        self.amplitude_slider.setMinimum(1)
        self.amplitude_slider.setMaximum(10)
        self.amplitude_slider.setValue(2)
        self.amplitude_slider.setStyleSheet("QSlider { background-color: #3a3a3a; }")
        self.amplitude_slider.valueChanged.connect(self.update_amplitude_scale)
        layout.addWidget(QLabel("Amplitude Scale"))
        layout.addWidget(self.amplitude_slider)

        self.point_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.point_size_slider.setMinimum(1)
        self.point_size_slider.setMaximum(50)
        self.point_size_slider.setValue(10)
        self.point_size_slider.setStyleSheet("QSlider { background-color: #3a3a3a; }")
        self.point_size_slider.valueChanged.connect(self.update_point_size)
        layout.addWidget(QLabel("Point Size"))
        layout.addWidget(self.point_size_slider)

        self.process_btn = QPushButton("Process")
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #00cc00; border-radius: 15px; padding: 10px;
                font-size: 12px; color: #ffffff;
            }
            QPushButton:hover { background-color: #00e600; }
            QPushButton:disabled { background-color: #666666; }
        """)
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("QProgressBar { border-radius: 5px; } QProgressBar::chunk { background-color: #00cc00; }")
        layout.addWidget(self.progress)

        self.setLayout(layout)
        self.setAcceptDrops(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(30, 30, 30))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRect(0, 0, self.width(), self.height()), 50, 50)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.mp3'):
                self.audio_file = os.path.basename(file_path)
                shutil.copy(file_path, os.path.join(input_folder, self.audio_file))
                self.label.setText(f"Selected: {self.audio_file}")
                self.process_btn.setEnabled(True)
                break

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "MP3 Files (*.mp3)")
        if file_path:
            self.audio_file = os.path.basename(file_path)
            shutil.copy(file_path, os.path.join(input_folder, self.audio_file))
            self.label.setText(f"Selected: {self.audio_file}")
            self.process_btn.setEnabled(True)

    def choose_color(self):
        color = QColorDialog.getColor(self.color, self, "Select Visualizer Color")
        if color.isValid():
            self.color = color
            self.color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()}; border-radius: 15px; padding: 10px;
                    font-size: 12px; color: #ffffff;
                }}
                QPushButton:hover {{ background-color: {color.lighter(120).name()}; }}
            """)

    def update_amplitude_scale(self, value):
        self.amplitude_scale = value / 2.0

    def update_point_size(self, value):
        self.point_size = value

    def start_processing(self):
        fps = int(self.fps_combo.currentText().split()[0])
        res_text = self.res_combo.currentText()
        resolution = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4K": (3840, 2160)
        }[res_text.split()[0]]

        self.process_btn.setEnabled(False)
        self.progress.setValue(0)

        self.worker = Worker(self.audio_file, fps, resolution, self.color, self.amplitude_scale, self.point_size)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, message):
        self.label.setText(message)
        self.process_btn.setEnabled(True)
        self.progress.setValue(100)

    def on_error(self, message):
        self.label.setText(message)
        self.process_btn.setEnabled(True)
        self.progress.setValue(0)

    def clear_temp_frames(self):
        for file in os.listdir(temp_folder):
            os.remove(os.path.join(temp_folder, file))

    def closeEvent(self, event):
        self.clear_temp_frames()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GonioVisualizer()
    window.show()
    sys.exit(app.exec())