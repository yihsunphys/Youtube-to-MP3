import os
import io
import tempfile
import requests
from flask import Flask, request, render_template, jsonify, send_file
from dotenv import load_dotenv

load_dotenv()  # 載入 .env 文件
app = Flask(__name__)

# 使用 Render 提供的 PORT 環境變數
port = int(os.environ.get("PORT", 5000))

def get_youtube_title(youtube_id):
    """從 YouTube Data API 獲取影片標題"""
    api_url = f"https://www.googleapis.com/youtube/v3/videos"
    params = {
        'id': youtube_id,
        'part': 'snippet',
        'key': os.getenv('YOUTUBE_API_KEY')  # 需要在 .env 中提供 YouTube API 金鑰
    }
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["snippet"]["title"]
    return "downloaded_audio"  # 預設標題

def download_audio_to_disk(url):
    """從 YouTube URL 下載音訊檔案，並儲存在磁碟中"""
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

    # 下載 MP3 檔案並儲存到磁碟
    mp3_response = requests.get(download_link, stream=True)
    if mp3_response.status_code != 200:
        raise Exception("Failed to download audio file.")

    # 儲存 MP3 檔案至暫時檔案
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    with open(temp_file.name, 'wb') as f:
        for chunk in mp3_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    # 獲取影片標題作為檔名
    title = get_youtube_title(youtube_id)
    sanitized_title = ''.join(c for c in title if c.isalnum() or c in ' _-').strip()  # 移除非法字元
    filename = f"{sanitized_title}.mp3"

    return temp_file.name, filename

def youtube_parser(url):
    """從 YouTube URL 提取視頻 ID"""
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
        # 從 URL 下載檔案，並將其儲存在磁碟中
        file_path, filename = download_audio_to_disk(url)
        return send_file(
            file_path,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=filename  # 指定檔案名稱
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify({"status": "completed", "percentage": 100})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
