
import SwiftUI

struct ContentView: View {
    @State private var filePath = ""
    @State private var fps = 60
    @State private var resolution = "1920x1080"
    @State private var color = "#00FF00"
    @State private var amplitude: Float = 2.0
    @State private var pointSize: Float = 10.0
    @State private var format = "mp4"
    @State private var logOutput = "Waiting..."

    var body: some View {
        VStack(spacing: 12) {
            Text("🎛️ VizLab").font(.largeTitle)

            Button("Choose Audio File") {
                let panel = NSOpenPanel()
                panel.allowedContentTypes = [.audio]
                panel.allowsMultipleSelection = false
                if panel.runModal() == .OK {
                    filePath = panel.url?.path ?? ""
                }
            }

            Text("File: \(filePath)").font(.caption).foregroundColor(.gray)

            Picker("FPS", selection: $fps) {
                Text("30").tag(30)
                Text("60").tag(60)
                Text("120").tag(120)
            }

            Picker("Resolution", selection: $resolution) {
                Text("720p").tag("1280x720")
                Text("1080p").tag("1920x1080")
                Text("4K").tag("3840x2160")
            }

            TextField("Color Hex", text: $color)
                .textFieldStyle(RoundedBorderTextFieldStyle())

            Slider(value: $amplitude, in: 0.5...10.0, step: 0.1)
            Text("Amplitude: \(amplitude, specifier: "%.1f")")

            Slider(value: $pointSize, in: 1...50, step: 1)
            Text("Point Size: \(pointSize, specifier: "%.0f")")

            Picker("Format", selection: $format) {
                Text("MP4").tag("mp4")
                Text("MOV").tag("mov")
                Text("AVI").tag("avi")
            }

            Button("🎬 Process with VizLab") {
                runVizLab()
            }

            Divider().padding(.top, 10)

            ScrollView {
                Text(logOutput)
                    .font(.system(size: 10, design: .monospaced))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(Color.black.opacity(0.1))
                    .cornerRadius(8)
            }.frame(height: 150)
        }
        .padding()
        .frame(width: 450)
    }

    func runVizLab() {
        guard !filePath.isEmpty else {
            logOutput = "⚠️ Please select an audio file."
            return
        }

        guard let pythonPath = Bundle.main.path(forResource: "venv/bin/python3", ofType: "") else {
            logOutput = "❌ Could not find Python in venv"
            return
        }

        guard let scriptPath = Bundle.main.path(forResource: "vizlab", ofType: "py") else {
            logOutput = "❌ Could not locate vizlab.py"
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: pythonPath)
        process.arguments = [
            scriptPath,
            filePath,
            "\(fps)",
            resolution,
            color,
            "\(amplitude)",
            "\(pointSize)",
            format
        ]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        pipe.fileHandleForReading.readabilityHandler = { handle in
            if let output = String(data: handle.availableData, encoding: .utf8) {
                DispatchQueue.main.async {
                    logOutput += "\n" + output
                }
            }
        }

        do {
            try process.run()
            logOutput = "🚀 Running VizLab from venv..."
        } catch {
            logOutput = "❌ Failed to run: \(error.localizedDescription)"
        }
    }
}
