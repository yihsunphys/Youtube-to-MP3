import os
import subprocess
import threading
from flask import Flask, request, render_template, jsonify, send_from_directory
import shutil

app = Flask(__name__)
progress = {"status": "", "percentage": 0, "filename": ""}  # 加入 filename

# 使用 Render 提供的 PORT 環境變數
port = int(os.environ.get("PORT", 5000))

def clear_download_folder(folder):
    """清空指定資料夾"""
    if os.path.exists(folder):
        shutil.rmtree(folder)  # 刪除整個資料夾
    os.makedirs(folder)  # 重新建立空的資料夾

def download_audio(url, output_dir="downloads"):
    global progress
    clear_download_folder(output_dir)  # 清空資料夾
    progress["status"] = "Downloading"
    progress["percentage"] = 0

    # 使用 yt-dlp 來抓取影片標題
    command_title = ["yt-dlp", "--get-title", url]
    try:
        title_process = subprocess.Popen(command_title, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        title, _ = title_process.communicate()
        title = title.strip()  # 去除標題的空白字元
        if not title:
            title = "download"  # 如果標題為空，使用預設的檔案名
        
        # 動態設定檔案名稱，根據影片標題命名檔案
        output_file = os.path.join(output_dir, f"{title}.mp3")
        
        # 使用 yt-dlp 下載音訊並轉換為 mp3
        command = [
            "yt-dlp",
            "--cookies", "cookies.txt",
            "-x", "--audio-format", "mp3",
            "--output", output_file,
            url
        ]

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
            progress["filename"] = f"{title}.mp3"  # 設定檔案名稱
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
