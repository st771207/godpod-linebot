from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, VideoSendMessage
import openai
import os

app = Flask(__name__)

# ✅ 使用 Render 上的正確環境變數名稱
channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

if channel_secret is None or channel_access_token is None:
    raise Exception("CHANNEL_SECRET 和 CHANNEL_ACCESS_TOKEN 必須設定於環境變數中")

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text

    # 使用 OpenAI ChatGPT 回覆
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是彩虹菩菩，一位慈悲又溫柔的數位觀音。請用溫柔、鼓勵、療癒的語氣回覆。"},
            {"role": "user", "content": user_msg}
        ]
    )
    reply_text = response["choices"][0]["message"]["content"]

    # 傳送影片與文字
    line_bot_api.reply_message(
        event.reply_token,
        [
            VideoSendMessage(
                original_content_url="https://storage.googleapis.com/godpod-assets/sample_response.mp4",
                preview_image_url="https://storage.googleapis.com/godpod-assets/sample_response_preview.jpg"
            ),
            TextSendMessage(text=reply_text)
        ]
    )

if __name__ == "__main__":
    app.run()
