from fastapi import FastAPI, Request, Header, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from linebot.models import TextSendMessage, ImageMessage, VideoMessage, AudioMessage, LocationMessage, StickerMessage
from linebot.models import FollowEvent, FlexSendMessage
from linebot.models import PostbackEvent, TextSendMessage
from starlette.exceptions import HTTPException
from dotenv import load_dotenv
import random
import os
import time
from game_config import profile_suzuki, profile_sasaki, prompt, storyline
from utils import game_start_button, game_end_button, get_button, get_image
from openai import OpenAI
import json

# .envファイルから環境変数を読み込む
load_dotenv()
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

app = FastAPI()
app.mount("/app/static", StaticFiles(directory="/app/static"), name="static")

# ユーザーの情報を保持する辞書
user_states = {}
user_data = {}
user_time = {}
button_last_timestamps = {}

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

# LINEからの受信イベントを処理する関数
@handler.add(MessageEvent)
def handle_message(event):
    global user_states
    global user_data
    global user_time

    # テキストメッセージの場合、handle_text_message 関数を実行
    if isinstance(event.message, TextMessage):
        handle_text_message(event)

    # テキストメッセージ以外の場合、再入力を促す
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="申し訳ありませんが、テキストのメッセージのみ対応しています。もう一度入力してください。")
        )


# 友達追加 or ブロック解除時のイベントを受け取る関数
@handler.add(FollowEvent)
def handle_follow(event):
    global user_states
    global user_data
    global user_time

    user_states[event.source.user_id] = 'not_started'

    # 送信するメッセージ
    greeting_message = TextSendMessage(text="学園ゲームで遊びながら、あなたのMBTIタイプを発見しましょう🏫🌟 この学園でのあなたの物語を通じて、自分自身をもっと深く知るチャンスです。準備はいいですか？それでは、スタートボタンを押して、ゲームを始めましょう！✨")
    
    # ゲームスタートボタン作成
    start_button = game_start_button()

    line_bot_api.reply_message(event.reply_token, [greeting_message, start_button])

# ボタンの処理
@handler.add(PostbackEvent)
def handle_postback(event):
    global user_states
    global user_data
    global user_time
    global button_last_timestamps

    user_id = event.source.user_id

    # 「ゲームを始める」が押された場合
    if event.postback.data == 'action=startGame' and user_states.get(user_id) == 'not_started':
        user_states[user_id] = 'started'

        user_data[user_id] = {"scene": "scene1", 
                              "step": "step1", 
                              "history": []
                              }

        gpt_message, image_message, button_message = game(user_id=user_id,
                                                          scene=user_data[user_id]["scene"], 
                                                          step=user_data[user_id]["step"], 
                                                          user_text="")
        
        if image_message and button_message:
            line_bot_api.reply_message(event.reply_token, [gpt_message, image_message, button_message])
        elif image_message and (not button_message):
            line_bot_api.reply_message(event.reply_token, [gpt_message, image_message])
        elif (not image_message) and button_message:
            line_bot_api.reply_message(event.reply_token, [gpt_message, button_message])
        elif (not image_message) and (not button_message):
            line_bot_api.reply_message(event.reply_token, [gpt_message])

    elif event.postback.data == 'action=startGame' and user_states.get(user_id) == 'started':
        pass

    # 「ゲームを終了する」が押された場合
    elif event.postback.data == 'action=endGame' and user_states.get(user_id) == 'started':
        user_states[user_id] = 'not_started'
        reply_message = TextSendMessage(text="ゲームを終了しました。また挑戦したい場合は、「ゲームを始める」ボタンを押してください。")
        start_button = game_start_button()
        line_bot_api.reply_message(event.reply_token, [reply_message, start_button])
    elif event.postback.data == 'action=endGame' and user_states.get(user_id) == 'not_started':
        pass

    # ゲーム中の場合
    elif user_states.get(user_id) == 'started':

        # ボタンのテキストを取得
        data = event.postback.data
        user_text = data.split('=')[1] if '=' in data else None

        # "end"の場合
        if user_data[user_id]["step"] == "END":
            mbti_message = MBTI(user_id)
            end_button = game_end_button()
            line_bot_api.reply_message(event.reply_token, [mbti_message, end_button])

        # "end"以外の場合
        elif user_data[user_id]["step"] != "END":
            gpt_message, image_message, button_message = game(user_id=user_id,
                                                          scene=user_data[user_id]["scene"],
                                                          step=user_data[user_id]["step"],
                                                          user_text=user_text)

            if image_message and button_message:
                line_bot_api.reply_message(event.reply_token, [gpt_message, image_message, button_message])
            elif image_message and (not button_message):
                line_bot_api.reply_message(event.reply_token, [gpt_message, image_message])
            elif (not image_message) and button_message:
                line_bot_api.reply_message(event.reply_token, [gpt_message, button_message])
            elif (not image_message) and (not button_message):
                line_bot_api.reply_message(event.reply_token, [gpt_message])

    # ゲームを始めていないかつ、ボタンが押された場合
    elif user_states.get(user_id) == 'not_started':
        pass


# テキストメッセージに対する処理
def handle_text_message(event):
    global user_states
    global user_data
    global user_time

    user_id = event.source.user_id
    user_text = event.message.text
    reply_message = None

    # ゲーム中の場合
    if user_states.get(user_id) == 'started':

        # "end"の場合
        if user_data[user_id]["step"] == "END":
            mbti_message = MBTI(user_id)
            end_button = game_end_button()
            line_bot_api.reply_message(event.reply_token, [mbti_message, end_button])

        # "end"以外の場合
        elif user_data[user_id]["step"] != "END":
            gpt_message, image_message, button_message = game(user_id=user_id,
                                                  scene=user_data[user_id]["scene"], 
                                                  step=user_data[user_id]["step"], 
                                                  user_text=None)
            if image_message and button_message:
                line_bot_api.reply_message(event.reply_token, [gpt_message, image_message, button_message])
            elif image_message and (not button_message):
                line_bot_api.reply_message(event.reply_token, [gpt_message, image_message])
            elif (not image_message) and button_message:
                line_bot_api.reply_message(event.reply_token, [gpt_message, button_message])
            else:
                line_bot_api.reply_message(event.reply_token, [gpt_message])

    # ゲームを始めていない場合
    elif user_states.get(user_id) == 'not_started':
        reply_message = TextSendMessage(text="ゲームを始める準備ができていません。まずは、「ゲームを始める」ボタンを押してください。")
        line_bot_api.reply_message(event.reply_token, [reply_message])


# -------------------------- 以下、ゲーム関数 --------------------------
def game(user_id, scene, step, user_text):
    global user_states
    global user_data
    global user_time

    # 初期化
    image_message = None
    button_message = None
    elapsed_time = None

    # 時間測定がある場合、end_timeを記録
    if user_time.get(user_id):
        user_time[user_id]["end_time"] = time.time()
        elapsed_time = user_time[user_id]["end_time"] - user_time[user_id]["start_time"]
        elapsed_time = round(elapsed_time)
        print(f"回答時間: {elapsed_time}秒")

        # 経過時間をuser_dataに追加
        # user_data[user_id]["elapsed_time"] = elapsed_time
         
        user_time.pop(user_id)

    # ユーザー会話履歴を取得
    history = user_data[user_id].get("history")

    # GPT-4を叩く
    gpt_text, next_scene, next_step, image_class, button, options, timecount = GPT(user_id, scene, step, user_text, history)

    # user_dataを更新
    user_data[user_id]["scene"] = next_scene
    user_data[user_id]["step"] = next_step
    if not (scene == "scene1" and step == "step1"): 
      if elapsed_time is not None:
        user_text = f"{user_text} (回答時間: {elapsed_time}秒)"
      tmp_history = {"gpt": gpt_text, "user": user_text}
      user_data[user_id]["history"].append(tmp_history)
    
    # gpt_textを変換
    gpt_message = TextSendMessage(text=gpt_text)

    # 画像がある場合、画像オブジェクトを取得
    if image_class:
        try:
            image_message = get_image(image_class)
        except:
            pass
    
    # ボタンがある場合、ボタンオブジェクトを取得
    if button:
        button_message = get_button(options)

    # 時間測定がある場合、start_timeを記録
    if timecount:
        user_time[user_id] = {"start_time": time.time()}

    return gpt_message, image_message, button_message
    
def GPT(user_id, scene, step, user_text, history):
    global user_states
    global user_data
    global user_time

    # system_promptが既に関連情報を含んだ辞書であると仮定
    system_prompt = {
        "prompt": prompt,
        "storyline": storyline,
        "profile_鈴木あい": profile_suzuki,
        "profile_佐々木美咲": profile_sasaki,
    }
    messages = [
    {"role": "system", "content": f"{system_prompt}"}
    ]

    # user_message, scene, および stepを辞書に組織し、ユーザーメッセージとして追加
    user_dict = {
        "user_id": user_id,
        "user_message": user_text,
        "scene": scene,
        "step": step,
        "history":history,
    }
    messages.append({"role": "user", "content": f"{user_dict}"})

    # GPT-4に対話履歴messagesを入力し、応答を取得
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={"type": "json_object"},
        messages=messages
    )

    # JSON形式で返される応答から情報を抽出
    generated_message_str= response.choices[0].message.content
    generated_message = json.loads(generated_message_str)
    print(generated_message_str)
    # 応答から必要な情報を取り出す
    gpt_text = generated_message.get("text")  
    next_scene = generated_message.get("next_scene") 
    next_step = generated_message.get("next_step")  
    image_class = generated_message.get("image_class") 
    button = generated_message.get("button") 
    options = generated_message.get("options")  
    timecount = generated_message.get("timecount")
    print("gpt_text_type: ", type(gpt_text))
    print("next_scene_type: ", type(next_scene))
    print("next_step_type: ", type(next_step))
    print("image_class_type: ", type(image_class))
    print("button_type: ", type(button))
    print("options_type: ", type(options))
    print("timecount_type: ", type(timecount))
    print("history:", history)


    # 応答情報を返す
    return gpt_text, next_scene, next_step, image_class, button, options, timecount

def MBTI(user_id):
    global user_states
    global user_data
    global user_time

    # ユーザの会話履歴のリストを取得
    history = user_data[user_id]["history"]

    # MBTIの結果を取得
    mbti_text = mbti_gpt(history)

    # MBTIの結果に基づいてメッセージを作成
    mbti_message = TextSendMessage(text=mbti_text)

    return mbti_message


def mbti_gpt(history):
    global user_states
    global user_data
    global user_time
    
    #プロンプト
    messages = [
	    {
	      "role": "user",
	      "content": "あなたは、会話履歴を基に、ユーザーのMBTIを診断するシステムです。\n\n会話履歴\nhistory:[{\"gpt\":gpt_text1, \"user\":user_text1}, {\"gpt\":gpt_text2, \"user\":user_text2}]\n\"gpt\"はgptが出力するテキストで、ユーザーへの質問\n\"user\"はgptの質問に対するユーザーの選択または回答"
	    },
	    {
	      "role": "user",
	      "content": f"会話履歴\nhistory:{history}\n\nこの会話履歴を基に、ユーザーの性格を判断し、なぜそのような診断結果になったのか、この性格タイプにはどのような特徴があるのかを説明してください。"
	    }
	  ]
        
	  # GPT-4に対話履歴messagesを入力し、応答を取得
    client = OpenAI()
    response = client.chat.completions.create(
        model = "gpt-4-turbo-preview",
        messages = messages
    )
    
    mbti_text = response.choices[0].message.content
    
    return mbti_text