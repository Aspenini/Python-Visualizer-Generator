# VizLab 🎛️

A cross-platform, audio-reactive visualizer generator using:

- 💻 SwiftUI frontend for macOS
- 🐍 Python backend (PyQt6, matplotlib, librosa)
- 🧳 Local venv packaging (no system Python needed)
- 🎨 Customizable output (resolution, color, amplitude, point size, format)

---

## 📦 Features

- Frame-by-frame polar gonio visualizer
- Multi-format audio input support (.mp3, .wav, .flac, etc.)
- Configurable output settings
- Cross-platform native experience:
  - SwiftUI GUI on macOS
  - PyQt6 GUI on Windows/Linux (planned)
  - macOS saves to `~/Library/Application Support/ApeXPloit Studios/VizLab`
  - Windows: `%APPDATA%\VizLab`
  - Linux: `~/.local/share/VizLab`

---

## 🚀 Getting Started (macOS)

```bash
chmod +x setup_venv.sh
./setup_venv.sh
```

Then open in Xcode and run the app.

---

## 🛠️ Project Structure

```
.
├── vizlab.py              # Python visualizer backend
├── setup_venv.sh          # Creates virtual environment + installs dependencies
├── venv/                  # Python environment (ignored in Git)
├── ContentView.swift      # SwiftUI user interface
├── VizLabApp.swift        # SwiftUI entry point
├── VizLab.xcodeproj/      # Xcode project
├── Assets.xcassets/       # App icons
├── Icon.png               # App branding icon
└── .gitignore
```

---

## ✍️ Credits

Made with ❤️ by ApeXPloit Studios

---

## 📜 License

MIT — free to use, remix, and vibe with.