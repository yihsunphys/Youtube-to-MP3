from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import subprocess
import threading

app = Flask(__name__)
progress = {"status": "", "percentage": 0}

# 使用 Render 提供的 PORT 环境变量
port = int(os.environ.get("PORT", 5000))

def download_audio(url, output_dir="downloads"):
    global progress
    os.makedirs(output_dir, exist_ok=True)
    progress["status"] = "Downloading"
    progress["percentage"] = 0

    command = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "-x", "--audio-format", "mp3",
        "--output", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            # 找到進度百分比，例如: "[download]  23.0%"
            if "[download]" in line and "%" in line:
                try:
                    percentage_str = line.split("%")[0].strip().split()[-1]  # 提取百分比部分
                    percentage = float(percentage_str)  # 轉換為浮點數
                    progress["percentage"] = int(percentage)  # 轉換為整數顯示
                except ValueError:
                    continue  # 如果無法解析，跳過該行

        stderr_output = process.stderr.read()
        process.wait()

        if process.returncode == 0:
            progress["status"] = "Completed"
            # 完成下载后，返回文件的路径
            filename = os.path.join(output_dir, "%(title)s.mp3")  # 假设是 mp3 文件
            return filename
        else:
            progress["status"] = f"Failed with error: {stderr_output}"
            return None
    except Exception as e:
        progress["status"] = f"Error: {str(e)}"
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    global progress
    url = request.form.get('url')
    output_dir = request.form.get('output_dir', "downloads")

    if not url:
        return jsonify({"error": "No URL provided!"}), 400

    progress = {"status": "Starting", "percentage": 0}
    # 在后台线程中下载文件并获取文件路径
    thread = threading.Thread(target=download_audio, args=(url, output_dir))
    thread.start()

    return jsonify({"message": "Download started!"})

@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(progress)

@app.route('/download-file/<filename>')
def download_file(filename):
    return send_from_directory(
        'downloads',          # 文件所在目录
        filename,             # 文件名
        as_attachment=True,   # 强制浏览器下载文件
        download_name=filename  # 设置下载时的文件名
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
