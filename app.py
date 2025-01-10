import os
import threading
import requests
from flask import Flask, request, render_template, jsonify, send_from_directory
import shutil
import hashlib

app = Flask(__name__)
progress = {"status": "", "percentage": 0, "filename": ""}  # 加入 filename

# 使用 Render 提供的 PORT 環境變數
port = int(os.environ.get("PORT", 5000))

def clear_download_folder(folder):
    """清空指定資料夾"""
    if os.path.exists(folder):
        shutil.rmtree(folder)  # 刪除整個資料夾
    os.makedirs(folder)  # 重新建立空的資料夾

def generate_filename(url):
    # 根據 URL 生成唯一檔名
    hash_object = hashlib.sha1(url.encode())
    filename = hash_object.hexdigest() + ".mp3"
    return filename

def download_audio(url, output_dir="downloads"):
    global progress
    clear_download_folder(output_dir)  # 清空資料夾
    progress["status"] = "Downloading"
    progress["percentage"] = 0

    # 從 YouTube URL 中提取視頻 ID
    youtube_id = youtube_parser(url)

    # 使用新的 API 進行下載
    api_url = 'https://youtube-mp36.p.rapidapi.com/dl'
    headers = {
        'X-RapidAPI-Key': os.getenv('VITE_RAPID_API_KEY'),
        'X-RapidAPI-Host': 'youtube-mp36.p.rapidapi.com'
    }
    params = {
        'id': youtube_id
    }

    try:
        # 發送請求到 API
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code == 200:
            # 解析 MP3 下載鏈接
            download_link = response.json().get('link')
            if download_link:
                filename = generate_filename(url)
                download_file(download_link, filename, output_dir)
                progress["status"] = "Completed"
                progress["filename"] = filename
            else:
                progress["status"] = "Failed to retrieve download link"
        else:
            progress["status"] = f"Error: {response.text}"
    except Exception as e:
        progress["status"] = f"Error: {str(e)}"

def youtube_parser(url):
    """從 YouTube URL 提取視頻 ID"""
    # 假設 URL 格式是 YouTube 的標準格式
    # https://www.youtube.com/watch?v=<video_id>
    video_id = url.split("v=")[-1]
    return video_id

def download_file(url, filename, output_dir):
    """下載文件並保存到指定路徑"""
    response = requests.get(url, stream=True)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

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
