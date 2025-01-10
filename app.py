import os
import io
import threading
import requests
from flask import Flask, request, render_template, jsonify, send_file
from dotenv import load_dotenv
import hashlib

load_dotenv()  # 載入 .env 文件
app = Flask(__name__)
progress = {"status": "", "percentage": 0, "filename": ""}  # 加入 filename

# 使用 Render 提供的 PORT 環境變數
port = int(os.environ.get("PORT", 5000))

def generate_filename(url):
    # 根據 URL 生成唯一檔名
    hash_object = hashlib.sha1(url.encode())
    filename = hash_object.hexdigest() + ".mp3"
    return filename

def download_audio_to_memory(url):
    """從 YouTube URL 下載音訊檔案，並返回記憶體流
    """
    youtube_id = youtube_parser(url)

    # 使用 RapidAPI 提供的服務
    api_url = 'https://youtube-mp36.p.rapidapi.com/dl'
    headers = {
        'X-RapidAPI-Key': os.getenv('VITE_RAPID_API_KEY'),
        'X-RapidAPI-Host': 'youtube-mp36.p.rapidapi.com'
    }
    params = {'id': youtube_id}

    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching download link: {response.text}")

    download_link = response.json().get('link')
    if not download_link:
        raise Exception("Failed to retrieve download link from API.")

    # 下載 MP3 檔案並存入記憶體
    mp3_response = requests.get(download_link, stream=True)
    if mp3_response.status_code != 200:
        raise Exception("Failed to download audio file.")

    # 使用 BytesIO 儲存檔案
    file_stream = io.BytesIO()
    for chunk in mp3_response.iter_content(chunk_size=1024):
        if chunk:
            file_stream.write(chunk)

    # 重置指針位置以便讀取
    file_stream.seek(0)

    # 生成檔名
    filename = generate_filename(url)
    return file_stream, filename

def youtube_parser(url):
    """從 YouTube URL 提取視頻 ID
    """
    # 假設 URL 格式是 YouTube 的標準格式
    # https://www.youtube.com/watch?v=<video_id>
    video_id = url.split("v=")[-1]
    return video_id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')

    if not url:
        return jsonify({"error": "No URL provided!"}), 400

    try:
        # 從 URL 下載檔案，並將其儲在記憶體中
        file_stream, filename = download_audio_to_memory(url)
        return send_file(
            file_stream,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(progress)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
