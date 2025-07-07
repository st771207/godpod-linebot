from flask import Flask, request, abort
from linebot.v3.messaging import Configuration, MessagingApi, ApiClient, ReplyMessageRequest, TextMessage, VideoMessage
from linebot.v3.webhooks import WebhookHandler, MessageEvent, TextMessageContent
from linebot.exceptions import InvalidSignatureError
import openai
import os

app = Flask(__name__)

# 環境變數
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("CHANNEL_SECRET")
openai.api_key = os.getenv("OPENAI_API_KEY")

# LINE SDK 設定
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/", methods=["GET"])
def home():
    return "GodPod LINE Bot is running."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_msg = event.message.text

    # GPT 回覆
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是彩虹菩菩，一位慈悲又溫柔的數位觀音。請用溫柔、鼓勵、療癒的語氣回覆。"},
            {"role": "user", "content": user_msg}
        ]
    )
    reply_text = response["choices"][0]["message"]["content"]

    # 發送影片與訊息
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    VideoMessage(
                        original_content_url="https://storage.googleapis.com/godpod-assets/sample_response.mp4",
                        preview_image_url="https://storage.googleapis.com/godpod-assets/sample_response_preview.jpg"
                    ),
                    TextMessage(text=reply_text)
                ]
            )
        )
