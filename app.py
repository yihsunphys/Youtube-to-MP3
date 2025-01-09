import os
import subprocess
import threading
from flask import Flask, request, render_template, jsonify, send_from_directory

app = Flask(__name__)
progress = {"status": "", "percentage": 0}

# 使用 Render 提供的 PORT 環境變數
port = int(os.environ.get("PORT", 5000))


def download_audio(url, output_dir="downloads"):
    global progress
    os.makedirs(output_dir, exist_ok=True)  # 確保下載目錄存在
    progress["status"] = "Downloading"
    progress["percentage"] = 0

    # 固定檔案名稱為 1.mp3
    output_file = os.path.join(output_dir, "1.mp3")
    command = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "-x", "--audio-format", "mp3",
        "--output", output_file,
        url
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            # 解析進度百分比，例如: "[download]  23.0%"
            if "[download]" in line and "%" in line:
                try:
                    percentage_str = line.split("%")[0].strip().split()[-1]  # 提取百分比部分
                    percentage = float(percentage_str)  # 轉換為浮點數
                    progress["percentage"] = int(percentage)  # 轉換為整數顯示
                except ValueError:
                    continue  # 如果無法解析，跳過該行
        process.wait()

        if process.returncode == 0:
            progress["status"] = "Completed"
        else:
            stderr_output = process.stderr.read()
            progress["status"] = f"Failed with error: {stderr_output}"
    except Exception as e:
        progress["status"] = f"Error: {str(e)}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    global progress
    url = request.form.get('url')

    if not url:
        return jsonify({"error": "No URL provided!"}), 400

    progress = {"status": "Starting", "percentage": 0}
    thread = threading.Thread(target=download_audio, args=(url,))
    thread.start()

    return jsonify({"message": "Download started!"})


@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(progress)


@app.route('/files/<filename>', methods=['GET'])
def get_file(filename):
    output_dir = "downloads"
    try:
        return send_from_directory(output_dir, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": "File not found"}), 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
