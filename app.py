import os
import requests
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()  # 載入 .env 文件
app = Flask(__name__)

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

def download_audio_to_link(url):
    """從 YouTube URL 下載音訊檔案，並返回下載鏈接"""
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

    return download_link

def youtube_parser(url):
    """從 YouTube URL 提取視頻 ID"""
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
        # 取得下載連結
        download_link = download_audio_to_link(url)
        return jsonify({"download_link": download_link})  # 返回下載連結給前端
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
