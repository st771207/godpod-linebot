from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ReplyMessageRequest, TextMessage, VideoMessage
from linebot.v3.webhooks import WebhookParser, MessageEvent, TextMessageContent
import openai
import os

app = Flask(__name__)

# 初始化 LINE Messaging API
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=channel_access_token)
line_bot_api = MessagingApi(configuration=configuration)
parser = WebhookParser(channel_secret)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("x-line-signature", "")
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except Exception as e:
        print("Webhook parse error:", e)
        abort(400)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            user_msg = event.message.text

            # ChatGPT 回覆
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是彩虹菩菩，一位慈悲又溫柔的數位觀音。請用溫柔、鼓勵、療癒的語氣回覆。"},
                    {"role": "user", "content": user_msg}
                ]
            )
            reply_text = response.choices[0].message.content

            # 回傳影片與文字訊息
            line_bot_api.reply_message(
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

    return "OK"

if __name__ == "__main__":
    app.run()
