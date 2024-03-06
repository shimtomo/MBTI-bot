from fastapi import FastAPI, Request, Header, BackgroundTasks
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from linebot.models import TextSendMessage, ImageMessage, VideoMessage, AudioMessage, LocationMessage, StickerMessage
from linebot.models import FollowEvent, FlexSendMessage
from linebot.models import PostbackEvent, TextSendMessage
from starlette.exceptions import HTTPException

from dotenv import load_dotenv
import os

# .envファイルから環境変数を読み込む
load_dotenv()
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

app = FastAPI()

# ユーザーの状態を保持する辞書
user_states = {}

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
    # ユーザーIDを取得
    user_id = event.source.user_id
    print(f"User ID: {user_id}")

    # 受け取ったメッセージをそのまま返信
    message_text = event.message.text
    reply_message = TextSendMessage(text=f"{message_text}")
    line_bot_api.reply_message(event.reply_token, reply_message)


# 友達追加 or ブロック解除時のイベントを受け取る関数
@handler.add(FollowEvent)
def handle_follow(event):

    # ユーザーをゲーム未開始状態に設定
    user_states[event.source.user_id] = 'not_started'

    # 送信するメッセージ
    greeting_message = TextSendMessage(text="学園ゲームで遊びながら、あなたのMBTIタイプを発見しましょう🏫🌟 この学園でのあなたの物語を通じて、自分自身をもっと深く知るチャンスです。準備はいいですか？それでは、スタートボタンを押して、ゲームを始めましょう！✨")
    
    # 送信する
    flex_message = FlexSendMessage(
        alt_text='ゲームを始めよう',
        contents={
          "type": "bubble",
          "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "ゲームを始める準備はできましたか？",
                "weight": "bold",
                "size": "md"
              },
              {
                "type": "button",
                "style": "primary",
                "action": {
                  "type": "postback",
                  "label": "ゲームを始める",
                  "data": "action=startGame"
                }
              }
            ]
          }
        }
    )

    line_bot_api.reply_message(event.reply_token, [greeting_message, flex_message])


# ボタンの処理
@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    print(f"User ID: {user_id}")
    print(f"User States: {user_states}")

    # 「ゲームを始める」が押された場合
    if event.postback.data == 'action=startGame' and (user_states.get(user_id) == 'not_started' or user_id not in user_states):
        user_states[user_id] = 'started'

        ####### game start #######
        # シーン1step1の実行
        #game()関数の実行
        ######

        # ゲーム終了メッセージを送信
        end_game_message = FlexSendMessage(
        alt_text='ゲームを終了する',
        contents={
              "type": "bubble",
              "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                  {
                    "type": "button",
                    "style": "primary",
                    "action": {
                      "type": "postback",
                      "label": "ゲームを終了する",
                      "data": "action=endGame"
                    }
                  }
                ]
              }
            }
        )
        line_bot_api.reply_message(event.reply_token, end_game_message)


    # 「ゲームを終了する」が押された場合
    elif event.postback.data == 'action=endGame' and user_states.get(user_id) == 'started':
        user_states[user_id] = 'not_started'
        reply_message = TextSendMessage(text="ゲームを終了しました。また挑戦したい場合は、「ゲームを始める」ボタンを押してください。")

        flex_message = FlexSendMessage(
            alt_text='ゲームを始める',
            contents={
              "type": "bubble",
              "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                  {
                    "type": "text",
                    "text": "ゲームを始める準備はできましたか？",
                    "weight": "bold",
                    "size": "md"
                  },
                  {
                    "type": "button",
                    "style": "primary",
                    "action": {
                      "type": "postback",
                      "label": "ゲームを始める",
                      "data": "action=startGame"
                    }
                  }
                ]
              }
            }
        )
        line_bot_api.reply_message(event.reply_token, [reply_message, flex_message])

