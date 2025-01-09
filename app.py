from flask import Flask, request, render_template, jsonify
import os
import subprocess
import threading






app = Flask(__name__)
progress = {"status": "", "percentage": 0}

# 使用 Render 提供的 PORT 环境变量
port = int(os.environ.get("PORT", 5000))

# @app.route('/')
# def home():
#     return "Hello, World!"

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=port)  # 绑定到所有可用IP和指定的端口

def download_audio(url, output_dir="downloads"):
    global progress
    os.makedirs(output_dir, exist_ok=True)
    progress["status"] = "Downloading"
    progress["percentage"] = 0

    command = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "--output", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            # 找到進度百分比，例如: "[download]  23.0%"
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
            progress["status"] = "Failed"
    except Exception as e:
        progress["status"] = f"Error: {e}"



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
    thread = threading.Thread(target=download_audio, args=(url, output_dir))
    thread.start()

    return jsonify({"message": "Download started!"})


@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(progress)


if __name__ == "__main__":
    app.run(debug=True)
