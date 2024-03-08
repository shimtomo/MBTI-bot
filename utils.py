from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from linebot.models import TextSendMessage, ImageMessage, VideoMessage, AudioMessage, LocationMessage, StickerMessage
from linebot.models import FollowEvent, FlexSendMessage
from linebot.models import PostbackEvent, TextSendMessage, ImageSendMessage

import random
import os
import time
from dotenv import load_dotenv

load_dotenv()
ngrok_url = os.getenv("NGROK_URL")

def game_start_button():
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
    return flex_message

def game_end_button():
    flex_message = FlexSendMessage(
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
    return flex_message



def get_button(options):
    """
    button==Trueのとき呼ばれる
    """

    # タイムスタンプを取得
    # timestamp = int(time.time())

    # Flex Messageのボディ部分を作成
    contents = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": []
        }
    }

    # optionsリストに基づいてボタンを追加
    for option in options:
        button_component = {
            "type": "button",
            "action": {
                "type": "postback",
                "label": option,
                "data": f"action={option}"
            }
        }
        contents["body"]["contents"].append(button_component)

    # Flex Messageを作成
    flex_message = FlexSendMessage(
        alt_text="選択肢を選んでください",
        contents=contents
    )

    return flex_message

def get_image(imageclass):
    
    directory = f"/app/static/{imageclass}"
    files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
    selected_file = random.choice(files)
    selected_file_path = f"{directory}/{selected_file}"

    selected_image_path=f"{ngrok_url}{selected_file_path}"

    image_message = ImageSendMessage(original_content_url=selected_image_path,
                                      preview_image_url=selected_image_path)
    return image_message



# def get_next_button():
#     # Flex Messageのボディ部分を作成
#     contents = {
#         "type": "bubble",
#         "body": {
#             "type": "box",
#             "layout": "vertical",
#             "contents": [
#                 {
#                     "type": "button",
#                     "style": "primary",
#                     "action": {
#                         "type": "postback",
#                         "label": "次へ",
#                         "data": "action=next"
#                     }
#                 }
#             ]
#         }
#     }

#     # Flex Messageを作成
#     flex_message = FlexSendMessage(
#         alt_text="次のステップに進む",
#         contents=contents
#     )

#     return flex_message