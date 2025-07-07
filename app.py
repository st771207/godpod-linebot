from flask import Flask, request, abort
from linebot.v3.webhooks import WebhookParser, MessageEvent, TextMessageContent
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
import openai
import os
import json

app = Flask(__name__)

channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")

configuration = Configuration(access_token=channel_access_token)
parser = WebhookParser(channel_secret)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except Exception as e:
        print("Webhook error:", e)
        abort(400)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            handle_message(event)

    return "OK"

def handle_message(event):
    user_msg = event.message.text

    # 呼叫 OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是彩虹菩菩，一位慈悲又溫柔的數位觀音。請用溫柔、鼓勵、療癒的語氣回覆。"},
            {"role": "user", "content": user_msg}
        ]
    )
    reply_text = response["choices"][0]["message"]["content"]

    # 傳送文字訊息
    with ApiClient(configuration) as api_client:
        line_api = MessagingApi(api_client)
        line_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    app.run()
