from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, VideoSendMessage
import os
import openai

# 初始化 Flask
app = Flask(__name__)

# 從環境變數取得 LINE & OpenAI 金鑰
channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not channel_secret or not channel_access_token or not openai_api_key:
    raise Exception("環境變數 CHANNEL_SECRET、CHANNEL_ACCESS_TOKEN、OPENAI_API_KEY 必須設定")

# 初始化 LINE SDK（仍為 v2 語法）
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# 初始化新版 OpenAI 客戶端
client = openai.OpenAI(api_key=openai_api_key)

# LINE webhook 接收點
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 處理 LINE 使用者文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text

    # 使用 OpenAI GPT 回覆
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是彩虹菩菩，一位慈悲又溫柔的數位觀音。請用溫柔、鼓勵、療癒的語氣回覆。"},
            {"role": "user", "content": user_msg}
        ]
    )
    reply_text = response.choices[0].message.content

    # 傳送影片與文字回覆
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
