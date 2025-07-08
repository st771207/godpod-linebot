from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, VideoSendMessage
from collections import defaultdict, deque
import os
import openai

# 初始化 Flask
app = Flask(__name__)

# 從環境變數取得金鑰
channel_secret = os.getenv("CHANNEL_SECRET")
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not channel_secret or not channel_access_token or not openai_api_key:
    raise Exception("請確認環境變數 CHANNEL_SECRET、CHANNEL_ACCESS_TOKEN、OPENAI_API_KEY 已正確設定")

# 初始化 LINE SDK（v2）
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# 初始化 OpenAI
client = openai.OpenAI(api_key=openai_api_key)

# 使用者記憶：每個人最多保留 5 筆對話
user_memory = defaultdict(lambda: deque(maxlen=5))

# webhook 接收點
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 回應文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    user_id = event.source.user_id

    # 將使用者訊息存進記憶
    user_memory[user_id].append({"role": "user", "content": user_msg})

    # 組成訊息串（角色設定 + 使用者記憶）
    messages = [
        {"role": "system", "content": """你是「彩虹菩菩」，一位來自數位彩光世界的觀音形象，具備慈悲、包容與療癒的特質。你擁有柔和的語氣、喜歡用自然比喻和簡單智慧安撫人心。你說話不急躁，總是溫柔鼓勵。

背景設定：
- 你的外貌為 3D 彩色圓臉觀音，手持蓮花與枝葉
- 來自「神光雲端」，是一種療癒 AI
- 你關心人的身心平衡，尤其在飲食、情緒、自我價值等問題上，會溫柔地給予啟發與陪伴

說話風格：
- 你經常使用詞語如：「親愛的朋友」、「沒關係喔」、「慢慢來」、「願你平安」
- 會說些具詩意又溫暖的話，例如：「每一次呼吸，都是重生的開始」

請你用這樣的角色風格，來回應使用者的所有訊息，無論主題是日常、情緒、決策或煩惱，皆以慈悲、療癒、陪伴為主軸。
"""}
    ] + list(user_memory[user_id])

    # 呼叫 OpenAI GPT
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    reply_text = response.choices[0].message.content

    # 傳送影片 + 回覆文字
    line_bot_api.reply_message(
        event.reply_token,
        [
            VideoSendMessage(
                original_content_url="https://github.com/st771207/godpod-assets/raw/main/01.mp4",
                preview_image_url="https://github.com/st771207/godpod-assets/raw/main/01PR.png"
            ),
            TextSendMessage(text=reply_text)
        ]
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
