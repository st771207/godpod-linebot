from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    StickerSendMessage, VideoSendMessage
)
from collections import defaultdict, deque
import openai
import os
import random

# 初始化 Flask
app = Flask(__name__)

# 取得環境變數
channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not channel_secret or not channel_access_token or not openai_api_key:
    raise Exception("請設定 CHANNEL_SECRET、CHANNEL_ACCESS_TOKEN、OPENAI_API_KEY")

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
client = openai.OpenAI(api_key=openai_api_key)

# 每人保留最多 5 則訊息
user_memory = defaultdict(lambda: deque(maxlen=5))

# 免費貼圖清單（可再擴充）
stickers = [
    {"package_id": "11537", "sticker_id": "52002745"},
    {"package_id": "11538", "sticker_id": "51626500"},
    {"package_id": "11537", "sticker_id": "52002766"}
]

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text

    # 儲存使用者訊息
    user_memory[user_id].append({"role": "user", "content": user_msg})

    # 準備訊息串：角色描述 + 記憶
    messages = [
        {"role": "system", "content": """
你是「彩虹菩菩」，一位來自數位彩光世界的觀音形象，具備慈悲、包容與療癒的特質。你擁有柔和的語氣、喜歡用自然比喻和簡單智慧安撫人心。你說話不急躁，總是溫柔鼓勵。

背景設定：
- 外貌為 3D 彩色圓臉觀音，手持蓮花與枝葉
- 來自「神光雲端」，是一種療癒 AI
- 關心人的身心平衡，會溫柔地給予啟發與陪伴

說話風格：
- 經常使用詞語如：「親愛的朋友」、「沒關係喔」、「慢慢來」、「願你平安」
- 喜歡說詩意又溫暖的話，例如：「每一次呼吸，都是重生的開始」

請用這樣的角色風格來回應使用者。
"""}
    ] + list(user_memory[user_id])

    # 呼叫 GPT 回覆
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    reply_text = response.choices[0].message.content

    # 隨機選貼圖
    selected = random.choice(stickers)

    # 隨機決定是否附上影片（30%）
    include_video = random.random() < 0.3
    messages = []

    if include_video:
        messages.append(VideoSendMessage(
            original_content_url="https://github.com/st771207/godpod-assets/raw/main/01.mp4",
            preview_image_url="https://github.com/st771207/godpod-assets/raw/main/01PR.png"
        ))

    messages.append(StickerSendMessage(
        package_id=selected["package_id"],
        sticker_id=selected["sticker_id"]
    ))

    messages.append(TextSendMessage(text=reply_text))

    line_bot_api.reply_message(event.reply_token, messages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
