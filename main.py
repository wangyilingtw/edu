from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import requests

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

@app.route("/search_and_summarize", methods=["POST"])
def search_and_summarize():
    data = request.json
    topic = data.get("topic")
    if not topic:
        return jsonify({"error": "Missing topic"}), 400

    search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={topic}&type=video&maxResults=1&key={YOUTUBE_API_KEY}"
    try:
        res = requests.get(search_url)
        search_data = res.json()

        # 加上 YouTube API 錯誤輸出
        if res.status_code != 200:
            print(f"🔴 YouTube API Error: Status {res.status_code}")
            print(f"🔴 Response: {search_data}")

        if 'items' not in search_data or not search_data['items']:
            return jsonify({"error": "No video found for this topic."}), 404

        selected_video = search_data['items'][0]
    except Exception as e:
        print(f"🔴 Search error: {e}")
        return jsonify({"error": f"Search error: {str(e)}"}), 500

    video_id = selected_video['id']['videoId']
    title = selected_video['snippet']['title']
    description = selected_video['snippet']['description']

    try:
        stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={YOUTUBE_API_KEY}"
        stats_res = requests.get(stats_url).json()
        view_count = stats_res['items'][0]['statistics'].get('viewCount', '0')
    except Exception as e:
        print("🔴 View count error:", e)
        view_count = "0"

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
        summary = f"GPT summary failed: {str(e)}"

    try:
        image_response = openai.Image.create(
            prompt=f"Photo-realistic, cinematic cover image for: {title}. Use real-world lighting, high definition detail, natural environment, modern people in work/study setting, horizontal layout, sharp photo-style rendering.",
            n=1,
            size="512x512"
        )
        image_url = image_response["data"][0]["url"]
    except Exception as e:
        print("🔴 Image generation error:", e)
        image_url = ""

    return jsonify({
        "video_id": video_id,
        "title": title,
        "summary": summary,
        "viewCount": view_count,
        "coverImage": image_url
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
