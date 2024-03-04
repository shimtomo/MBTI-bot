from fastapi import FastAPI, Request, Header, BackgroundTasks
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from linebot.models import TextSendMessage, ImageMessage, VideoMessage, AudioMessage, LocationMessage, StickerMessage
from starlette.exceptions import HTTPException

from dotenv import load_dotenv
import os

# .envファイルから環境変数を読み込む
load_dotenv()
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

app = FastAPI()
  
@app.post("/callback")
async def callback(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature=Header(None),
):
    body = await request.body()

    try:
        background_tasks.add_task(
            handler.handle, body.decode("utf-8"), x_line_signature
        )
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "ok"

# LINEからのメッセージを受け取る関数
@handler.add(MessageEvent)
def handle_message(event):
    
    # テキストメッセージの場合、特定の処理を行う
    if isinstance(event.message, TextMessage):
        handle_text_message(event)

    # テキストメッセージ以外の場合、再入力を促す
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="申し訳ありませんが、テキストのメッセージのみ対応しています。もう一度入力してください。")
        )

# テキストメッセージに対する処理を実装
def handle_text_message(event):
    print(event.message.text)
    message = TextMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)

