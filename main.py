from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import requests
import random

app = Flask(__name__)
CORS(app, resources={r"/search_and_summarize": {"origins": "https://edu-1-r9og.onrender.com"}})

openai.api_key = os.environ.get("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/search_and_summarize", methods=["POST"])
def search_and_summarize():
    data = request.json
    topic = data.get("topic")
    if not topic:
        return jsonify({"error": "Missing topic"}), 400

    # YouTube 搜尋，獲取最多 10 個結果並隨機選擇
    search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={topic}&type=video&maxResults=10&key={YOUTUBE_API_KEY}"
    try:
        res = requests.get(search_url)
        search_data = res.json()

        if res.status_code != 200:
            print(f"🔴 YouTube API Error: Status {res.status_code}")
            print(f"🔴 Response: {search_data}")
            return jsonify({"error": "YouTube API error"}), 500

        if 'items' not in search_data or not search_data['items']:
            print("🔴 No videos found for topic:", topic)
            return jsonify({"error": "No video found for this topic."}), 404

        # 隨機選擇一個影片
        selected_video = random.choice(search_data['items'])
    except Exception as e:
        print(f"🔴 Search error: {e}")
        return jsonify({"error": f"Search error: {str(e)}"}), 500

    video_id = selected_video['id']['videoId']
    title = selected_video['snippet']['title']
    description = selected_video['snippet']['description']
    # 使用 YouTube 原生縮圖
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    # 獲取影片統計資訊（觀看次數）
    try:
        stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={YOUTUBE_API_KEY}"
        stats_res = requests.get(stats_url).json()
        view_count = stats_res['items'][0]['statistics'].get('viewCount', '0')
    except Exception as e:
        print("🔴 View count error:", e)
        view_count = "0"

    # 生成 AI 摘要
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Summarize the following YouTube video description into 3 to 5 bullet points in clear English. Each point should be no more than 15 words. Begin each point with a dash ('-')."
                },
                {
                    "role": "user",
                    "content": description[:3000]
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        print("🔴 Summary error:", e)
        summary = f"Summary failed: {str(e)}"

    return jsonify({
        "video_id": video_id,
        "title": title,
        "summary": summary,
        "viewCount": view_count,
        "thumbnail": thumbnail_url
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
