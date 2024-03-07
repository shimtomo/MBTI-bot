from fastapi import FastAPI, Request, Header, BackgroundTasks
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
# import openai

# .envファイルから環境変数を読み込む
load_dotenv()
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

app = FastAPI()

# ユーザーの情報を保持する辞書
user_states = {}
user_data = {}

# gameの設定
profile_suzuki={
    "profile":"鈴木あいは、信頼性と責任感が人一倍強いISTJタイプの学生です。雪が静かに降り積もる冬の日に生まれ、自然と秩序を好む性格を持っています。学生生活では、成績優秀でありながらも、クラスメイトや友人たちからは、その頼りがいのある性格で知られています。彼女は学業においても個人の趣味においても、計画的に物事を進めることを好み、図書館での研究や、集中して勉強する時間を大切にしています。土日には、ローカルのボランティア活動や、学校のクラブ活動に積極的に参加し、コミュニティへの貢献を重んじる姿勢を見せます。",
    "personality":"鈴木あいは、細部に注意を払い、任務が完璧に完成することを求めます。クラスメイトからのグループプロジェクトでリーダー役を引き受けることもしばしばあり、その際にはプロジェクトの各ステップを念入りに計画し、チーム全体を成功に導きます。彼女は静かで真面目な性格ですが、友人や同級生との深い絆を大切にしており、必要とされればいつでも支援を惜しみません。変化に対してはやや慎重で、新しいアイデアや提案に対しては、それが実際に機能するかどうかをよく考えた上で受け入れる傾向にあります。",
    "lines":"鈴木あいは、話すときには落ち着いており、自分の言葉を慎重に選びます。「先生のアドバイスに従って、このレポートを改善するつもりです」「実績に基づいたこの方法で、私たちのプロジェクトは成功するはずです」といった風に、論理的で具体的な表現を用いてコミュニケーションを取ります。彼女は自分の感情をあまり表に出さず、むしろ合理的な議論や事実に基づく情報交換を好みます。しかし、友人との会話では、時には温かい笑顔を見せたり、冗談を言ったりして、周りを安心させることもあります。}"
}
profile_sasagi={
    "profile":"佐々木美咲は、まるで太陽のように明るく、周りを照らすENFPタイプの魂の持ち主です。彼女は、人生を大冒険と捉え、常に新しいことにチャレンジすることを恐れません。彼女は写真家、ブロガー、そしてソーシャルメディアのインフルエンサーとして活躍し、世界中の美しい瞬間を捉え、それを共有することで多くの人々にインスピレーションを与えています。フリーランスのライフスタイルを全力で楽しみ、彼女の作品は常に新鮮で、心を動かすものです。",
    "personality":"佐々木美咲は、いつも笑顔で、どんな状況でもポジティブな面を見つけ出す天才です。人との会話を楽しみ、どこへ行っても友達を作ることができる社交的な性格をしています。彼女は常に自分の感情をオープンにし、他人の話に真剣に耳を傾け、心からの支援を惜しみません。創造性に富んでおり、思いがけないアイデアで人々を驚かせることもしばしば。彼らはルーチンを嫌い、日々の生活に小さな冒険を見つけ出しては、それを楽しむことに喜びを見出します。",
    "lines":"佐々木美咲は、話すときにはまるで物語を紡ぐかのよう。彼女の言葉は常に温かく、聞いている人を元気づけ、勇気づけます。「ねえ、一緒に世界をもっとカラフルにしようよ！」「大丈夫、君ならできるよ！」といった励ましの言葉を自然と口にし、周りの人々にポジティブなエネルギーを分け与えます。彼女は自分の感情を素直に表現し、その真っ直ぐな言葉が人々の心に響きます。"
}

prompt="""
Now You (GPT) are a game system.
It's up to you to decide the game output. You will be output in JSON format, including "text", "next_step", "next_scene", "image_class", "botton", "options", "timecount".
Firstly, you will be provided with a dictionary named "storyline" which is the script of the story.
It contains "scene" and "step" and details for each step. We will play the game step by step through dialogue. The following are the rules:
At each step of the "storyline":
The key "description" is a narration, acting like dialogue in the game. What you have to do is to directly output the value of "description" into "text" remaining unchanged.
The key "next" indicates the next step of the current step. When the value of "next" contains only "step", that means moving to the specific step of the same scene where the current step took place. However, when the value of "next" contains both "scene" and "step", it means the scene is gonna change.
The value of the key "GPT_chararter" represents the role that GPT needs to play in this step. Please play the role you according to the profile, personality and lines in the dictionaries "profile_鈴木あい" and "profile_佐々木美咲". Be as vivid as possible.
The key "GPT_talk" represents that what the content will be in this conversation.
The key "GPT_next" means to let GPT determine whether the current conversation needs to continue. If it continues, continue the current conversation without moving on to the next step.  If GPT determines that the conversation should be ended, follow the value of the key "next" to enter the next step.
Output the value of key "botton" into "botton" in your answer.
Output the value of key "answer" into "answer" in your answer.
Output the value of key "options" into "options" in your answer.
The key "image" indicates whether an image needs to be output in the current step. When "image" is True, output the value of "image_class" into "image_class" in your JSON file.
Output the value of key "timecount" into "timecount" in your answer.
In addition, in each input prompt:
The key "user_id" is the user's ID. This is a multiplayer game, so you need to remember all the  different player IDs and players'progress.
The key "user_message" is the user's answer. If the user's answer is "次へ", then move to the next step/scene according to the value "next".
Remember, if the user entered his or her name, any mention of the user in subsequent scripts will automatically be replaced by the user's entered name.
The key "history" is the history of your conversation, please refer to
"""

storyline = {
    "scene1": {
        "step1": {
            "description": "新しい学校の初日、私は緊張で胸がいっぱいだった。教室の扉を開けると、すでに授業が始まる準備が整っている。",
            "button": True
        },
        "step2": {
            "description": "私は担任の先生に連れられて、前へと進んだ。先生が私をクラスメイトに紹介し始めた時、教室は静かになり、すべての目が私に注がれた。",
            "button": True
        },
        "step3": {
            "description": "先生：「みなさん、今日は新しい転校生が来ました。彼が自己紹介をするので、よく聞いてあげてください。」"
        },
        "step4": {
            "description": "先生：「どうぞ」",
            "answer": True,
            "next": "step5"
        },
        "step5": {
            "description": "自己紹介が終わると、クラスメイトから温かい拍手が送られた。その瞬間、私の緊張は少し解け、心が温かくなった。",
            "button": True,
            "next": "step6"
        },
        "step6": {
            "description": "先生も優しい笑顔で、「ありがとう。さて、次に大切なことがあります。現在、クラスには二つの空席がありますが、どちらか一つを選んで、あなたの席になってもらいたいと思います。」",
            "image": True,
            "image_class": "character",
            "button": True,
            "timecount": True,
            "options": ["左の子", "右の子"],
            "next": {
                "左の子": "scene2,step1",
                "右の子": "scene2,step3"
            }
        }
    },
    "scene2": {
        "step1": {
            "description": "隣には、すでに座っている女子生徒がいた。彼女は静かにノートを取り出していた。私は少し緊張しながらも、隣の席の彼女に話しかけるべきかどうか迷っていた。",
            "button": True,
            "timecount": True,
            "options": ["話をかける", "話をかけない"],
            "next": {
                "話をかける": "scene2,step2",
                "話をかけない": "scene2,step7"
            }
        },
        "step2": {
            "answer": True,
            "GPT_character": "鈴木あい",
            "GPT_talk": "趣味について話す",
            "GPT_next": True,
            "next": "step6"
        },
        "step3": {
            "description": "隣に座っていた女子生徒が目を輝かせながら私に声をかけてきた。「こんにちは！私、佐々木美咲。このクラスで一緒になれてうれしいな。{user}さんの自己紹介、聞かせてもらったよ。」",
            "answer": True,
            "GPT_character": "佐々木美咲",
            "GPT_talk": "趣味について話す",
            "GPT_next": True,
            "next": "step4"
        },
        "step4": {
            "description": "明日まで出す課題が出され、下校のベルが鳴った。美咲が私に向かって、ニコニコしながら提案してきた。美咲：「ねえ、{user}さん、一緒に帰らない？」",
            "button": True,
            "next": "step5"
        },
        "step5": {
            "description": "私は美咲の提案に心から喜んだ。新しい学校で、こんなに早く友達ができるなんて思ってもみなかったからだ。しかし、美咲はさらに一歩進んで提案してきた。美咲：「他のクラスメートも誘ってみようか？それとも、今日は私たちだけで帰って、次回から他のみんなも一緒にしようか？」",
            "button": True,
            "timecount": True,
            "options": ["美咲と一緒に帰る", "みんなと一緒に帰る"],
            "next": {
                "美咲と一緒に帰る": "scene3,step1",
                "みんなと一緒に帰る": "scene3,step2"
            }
        },
        "step6": {
            "description": "会話が途中で中断され、先生が夏休みの宿題の提出を促してきた。宿題が多く、提出するのにも時間がかかった。あいがため息をつきながら言った：「疲れたー。{user}さん、夏休みの宿題、どうやって終わらせました？私は計画を立てて、毎日ちょっとずつ取り組んでいました。」",
            "answer": True,
            "GPT_character": "鈴木あい",
            "GPT_talk": "夏休みの宿題の完成方法について話す",
            "GPT_next": True,
            "next": "scene3,step3"
        },
        "step7": {
            "description": "しばらくの間、静かに自分の持ち物を整理しながら、新しいクラスの雰囲気に慣れようと思った。しかし、その沈黙は長くは続かなかった。授業が始まる直前、隣の女子生徒が優しく私に話しかけてきた。鈴木あい：「転校生ですよね？私、鈴木あい。クラスで一緒になれて嬉しいです。」",
            "answer": True,
            "GPT_character": "鈴木あい",
            "GPT_talk": "趣味について話す",
            "GPT_next": True,
            "next": "step8"
        },
        "step8": {
            "description": "会話が途中で中断され、先生が夏休みの宿題の提出を促してきました。その時、あいがバッグを必死に探し始めたのに気づきました。彼女の表情が次第に焦りと不安で曇っていくのが見て取れました。そして、彼女は私に向かって、慌てた声でささやきました：「やばい、宿題を持ってくるのを忘れた...泣きそう。」",
            "answer": True,
            "GPT_character": "鈴木あい",
            "GPT_next": True,
            "next": "scene3,step3"
        }
    },
    # 继续之前的storyline字典
    "scene3": {
        "step1": {
            "description": "美咲と一緒に帰る途中で、町中にあるおいしそうなレストランを見つけました。店の前を通ると、美味しそうな匂いが漂ってきて、私たちの足を自然と止めさせました。美咲が私に向かって質問してきました。「うわー、おしゃれなレストラン！入ってみない？課題があるから時間が遅くなっちゃうけど、大丈夫かな？」",
            "image": True,
            "image_class": "restaurant",
            "timecount": True,
            "options": ["いいよ", "やはり速く課題をやりたいから今日はやめる"],
            "next": {
                "いいよ": "scene4,step1",
                "やはり速く課題をやりたいから今日はやめる": "END"
            }
        },
        "step2": {
            "description": "みんなと一緒に帰る途中で、町中にあるおいしそうなレストランを見つけました。店の前を通ると、美味しそうな匂いが漂ってきて、私たちの足を自然と止めさせました。美咲がみんなに向かって質問してきました。「うわー、おしゃれなレストラン！入ってみない？課題があるから時間が遅くなっちゃうけど、大丈夫かな？」",
            "image": True,
            "image_class": "restaurant",
            "timecount": True,
            "options": ["いいよ", "やはり速く課題をやりたいから今日はやめる"],
            "next": {
                "いいよ": "scene4,step2",
                "やはり速く課題をやりたいから今日はやめる": "END"
            }
        },
        "step3": {
            "description": "放課後、あいと一緒に帰ることとなり、途中で町中にあるおいしそうなレストランを見つけました。店の前を通ると、美味しそうな匂いが漂ってきて、私たちの足を自然と止めさせました。その誘惑には抗えず、私たちは言葉を交わす間もなく自然と店内へと足を踏み入れました。",
            "image": True,
            "image_class": "restaurant",
            "button": True,
            "next": "scene4,step3"
        }
    },
    "scene4": {
        "step1": {
            "description": "美咲と一緒にレストランに入ると、私たちは温かく迎え入れられ、席に案内されました。テーブルに着くと、ウェイターがメニューを持ってきてくれました。メニューを開いてみると、さまざまな美味しそうな料理が並んでいて、選ぶのが難しいほどでした。",
            "button": True,
            "next": "step2"
        },
        "step2": {
            "description": "メニューは以下の通りです。好きな一品をお選びください。",
            "timecount": True,
            "button": True,
            "image": True,
            "options": {
                "1.特製ハンバーグステーキ": "自家製ソースで仕上げたジューシーなハンバーグ。付け合わせには、季節の野菜とマッシュポテトが添えられています。",
                "2.鶏のクリーム煮": "柔らかく煮込んだ鶏肉を、濃厚なクリームソースで味わう一品。バゲットが付いてきます。",
                "3.海鮮パエリア": "新鮮な海の幸がふんだんに使われた、彩り豊かなスペイン料理。サフランの香りが食欲をそそります。",
                "4.野菜たっぷりグリーンカレー": "辛さ控えめのココナッツベースのカレー。たくさんの種類の野菜が入っていて、ヘルシーです。",
                "5.マルゲリータピザ": "シンプルながらも、トマトの酸味とモッツァレラチーズの濃厚さが絶妙なバランスのピザ。"
            },
            "image_class": {
                "特製ハンバーグステーキ": "hamburger_steak",
                "鶏のクリーム煮": "cream_chicken",
                "海鮮パエリア": "seafood_paella",
                "野菜たっぷりグリーンカレー": "green_curry",
                "マルゲリータピザ": "margherita_pizza"
            },
            "next": "END"
        }
    }
}


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




# テキストメッセージに対する処理を実装
def handle_text_message(event):
    # ユーザーIDを取得
    user_id = event.source.user_id
    print(f"User ID: {user_id}")

    # 受け取ったメッセージをそのまま返信
    user_text = event.message.text
    # reply_message = TextSendMessage(text=f"{user_text}")
    reply_message = None

    if user_states.get(user_id) == 'started':
        user_data = get_user_data(user_id)
        print(f"User data: {user_data}")
        # scene = user_data.get("scene")
        # step = user_data.get("step")
        scene = 1
        step = 1

        gpt_message, image_path, button_message = game(user_id=user_id, scene=scene, step=step, user_text=user_text if user_text else None)
        reply_message = TextSendMessage(text=gpt_message)

        # user の step が "end"の場合
        if step == "end":
            #ゲーム終了メッセージを送信
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
            line_bot_api.reply_message(event.reply_token, [reply_message, flex_message])
        else:
            line_bot_api.reply_message(event.reply_token, [reply_message])

    elif user_states.get(user_id) == 'not_started' or user_id not in user_states:
        reply_message = TextSendMessage(text="ゲームを始める準備ができていません。まずは、「ゲームを始める」ボタンを押してください。")
        line_bot_api.reply_message(event.reply_token, [reply_message])

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
        user_data[user_id] = {"scene": 1, "step": 1, "history": []}
        
        gpt_message, image_path, button_message = game(user_id=user_id,
                                                        scene=user_data["user_id"]["scene"], 
                                                        step=user_data["user_id"]["scene"], 
                                                        user_text=None)
        ######

        gpt_message = TextSendMessage(text=gpt_message)

        line_bot_api.reply_message(event.reply_token, [gpt_message, button_message])



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

    # ゲーム中のボタン
    elif user_states.get(user_id) == 'started':
        user_data = get_user_data(user_id)
        print(f"User data: {user_data}")
        # scene = user_data.get("scene")
        # step = user_data.get("step")
        scene = 1
        step = 1

        gpt_message, image_path, button_message = game(user_id=user_id, scene=scene, step=step, user_text=None)
        reply_message = TextSendMessage(text=gpt_message)

        # user の step が "end" の場合
        if step == "end":

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
            line_bot_api.reply_message(event.reply_token, [reply_message, flex_message])
        else:
            line_bot_api.reply_message(event.reply_token, [reply_message])
      
    else:
        # ゲームを始めていないかつ、ボタンが押された場合
        pass



# button==Trueのとき呼ばれる
def game_button(options):
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



def game(user_id, scene, step, user_text):
    gpt_text, next_scene, next_step, image_class, button, options, timecount = GPT(user_id, scene, step, user_text)
    update_scene_step(user_id, next_scene, next_step)
    add_history(user_id, user_text, gpt_message)


    button_message = None
    image_path = None

    # ボタンがある場合
    if button:
        button_message = game_button(options)
    
    # 画像がある場合
    if image_class:
        image_path = get_image(image_class)

    return gpt_message, image_path, button_message
    
def GPT(user_id, scene, step, user_message, history):
    # system_promptが既に関連情報を含んだ辞書であると仮定
    system_prompt = {
        "prompt": prompt,
        "storyline": storyline,
        "profile_鈴木あい": profile_suzuki,
        "profile_佐々木美咲": profile_sasagi,
    }
    messages = [
    {"role": "system", "content": system_prompt}
    ]

    # user_message, scene, および stepを辞書に組織し、ユーザーメッセージとして追加
    user_dict = {
        "user_id": user_id,
        "user_message": user_message,
        "scene": scene,
        "step": step,
        "history":history,
    }
    messages.append({"role": "user", "content": user_dict})

    # GPT-4に対話履歴messagesを入力し、応答を取得
    response = openai.ChatCompletion.create(
        model="gpt-4",
        response_format={"type": "json_object"},
        messages=messages
    )

    # JSON形式で返される応答から情報を抽出
    generated_message = response["choices"][0]["message"]["content"]

    # 応答から必要な情報を取り出す
    gpt_text = generated_message["text"]
    next_scene = generated_message["next_scene"]
    next_step = generated_message["next_step"]
    image_class = generated_message["image_class"]
    button = generated_message["button"]
    options = generated_message["options"]
    timecount = generated_message["timecount"]

    # 応答情報を返す
    return gpt_text, next_scene, next_step, image_class, button, options, timecount

def get_image(imageclass):
    imagepass="app/images"
    imagefile=os.path.join(imagepass, imageclass)
    selected_image=random.choice(imagefile)
    return selected_image