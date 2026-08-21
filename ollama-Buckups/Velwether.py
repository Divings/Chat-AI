import requests
import os
import sys
import pickle
import configparser
import shutil
import pyfiglet


# =========================================================
# 画面クリア
# =========================================================

os.system("cls" if os.name == "nt" else "clear")


# =========================================================
# 定数
# =========================================================


CONFIG_DIR = "config"
DATA_DIR = "data"

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")
CHAT_LOG_FILE = os.path.join(DATA_DIR, "memory.vlm")

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


# =========================================================
# 設定データなどの移行
# =========================================================


if os.path.isfile("config.ini"):
    shutil.copyfile("config.ini",CONFIG_FILE)
    os.remove("config.ini")
    print("設定データを移行しました。")

if os.path.isfile("memory.vlm"):
    i=input(" 既存の記憶データを移行しますか? ( Y or N ) >> ")
    if i.lower()=="Y":
        if os.path.isfile(CHAT_LOG_FILE):
            print("")
            d=input(" 記憶データが既に存在します。上書きしますか? ( Y or N ) >> ")
            if i.lower()=="Y":
                shutil.copyfile("memory.vlm",CHAT_LOG_FILE)
                os.remove("memory.vlm")
            else:
                print(" 上書きをキャンセルしました")
        else:
            shutil.copyfile("memory.vlm",CHAT_LOG_FILE)
            os.remove("memory.vlm")
    else:
        print(" 記憶データの移行をキャンセルしました。")

# =========================================================
# config.ini チェック
# =========================================================

if not os.path.isfile(CONFIG_FILE):
    print(" config.iniファイルが見つかりません。")
    print("")
    print(" config.iniを作成してから、もう一度起動してください。")
    input(" >> ")
    sys.exit()


# =========================================================
# 設定ファイル読み込み
# =========================================================

def load_config():
    config = configparser.ConfigParser()

    with open(CONFIG_FILE, "r", encoding="utf-8") as configfile:
        config.read_file(configfile)

    return config


def load_model():
    """
    Ollamaで使用するモデル名を取得
    """
    config = load_config()

    try:
        return config["DEFAULT"]["model"]
    except KeyError:
        return "qwen3:1.7b"


def load_ollama_url():
    """
    Ollama API URL
    """
    config = load_config()

    try:
        return config["DEFAULT"]["ollama_url"]
    except KeyError:
        return "http://localhost:11434/api/chat"


def load_BotName():
    """
    Ollama Bot Name
    """
    config = load_config()

    try:
        return config["DEFAULT"]["bot_name"]
    except KeyError:
        return "ボット"

def load_preload():
    """
    起動時に自動で履歴を読み込むか
    1 = 自動読み込み
    0 = 毎回確認
    """
    config = load_config()

    try:
        return int(config["DEFAULT"]["preload"])
    except (KeyError, ValueError):
        return 0


def load_token():
    """
    Ollamaの最大生成トークン数
    """
    config = load_config()

    try:
        return int(config["DEFAULT"]["Max_Token"])
    except (KeyError, ValueError):
        return 1024


def load_system_prompt():
    config = load_config()

    bot_name = load_BotName()

    try:
        base_prompt = config["DEFAULT"]["system_prompt"]
    except KeyError:
        base_prompt = "あなたは自然な日本語を話すAIアシスタントです。"

    return (
        f"あなたの名前は「{bot_name}」です。"
        f"ユーザーはあなたを「{bot_name}」として扱います。"
        f"自分自身について話すときも、その名前と人格設定を維持してください。"
        f"{base_prompt}"
    )

# =========================================================
# 会話履歴
# =========================================================

def save_chat(messages):
    """
    会話履歴全体をmemory.vlmへ保存
    """

    try:
        with open(CHAT_LOG_FILE, "wb") as f:
            pickle.dump(messages, f)

    except Exception as e:
        print("")
        print(" 会話履歴の保存中にエラーが発生しました。")
        print(f" {e}")


def load_chat():
    """
    memory.vlmから会話履歴を読み込む
    """

    if not os.path.isfile(CHAT_LOG_FILE):
        return [
            {
                "role": "system",
                "content": load_system_prompt()
            }
        ]

    try:
        with open(CHAT_LOG_FILE, "rb") as f:
            messages = pickle.load(f)

        if not isinstance(messages, list):
            raise ValueError("memory.vlmの形式が正しくありません。")

        return messages

    except Exception as e:
        print("")
        print(" memory.vlmの読み込みに失敗しました。")
        print(f" {e}")
        print("")
        print(" 新しい会話として開始します。")

        return [
            {
                "role": "system",
                "content": load_system_prompt()
            }
        ]


def new_chat():
    """
    新規会話
    """

    return [
        {
            "role": "system",
            "content": load_system_prompt()
        }
    ]


# =========================================================
# Ollama確認
# =========================================================

def check_ollama():
    """
    Ollamaサーバーが起動しているか確認
    """

    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )

        if response.status_code == 200:
            return True

        return False

    except requests.exceptions.RequestException:
        return False


def check_model():
    """
    指定されたモデルがOllamaに存在するか確認
    """

    model = load_model()

    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )

        if response.status_code != 200:
            return False

        data = response.json()

        for item in data.get("models", []):
            name = item.get("name", "")

            if name == model:
                return True

        return False

    except requests.exceptions.RequestException:
        return False


# =========================================================
# Ollama チャット
# =========================================================

def chat_with_ollama(messages):
    """
    Ollamaへ会話履歴を送信
    """

    api_url = load_ollama_url()
    model = load_model()

    data = {
        "model": model,
        "messages": messages,
        "stream": False,

        "options": {
            "num_predict": load_token()
        }
    }

    try:
        response = requests.post(
            api_url,
            json=data,
            timeout=None
        )

    except requests.exceptions.ConnectionError:
        print("")
        print(" Ollamaに接続できませんでした。")
        print("")
        print(" Ollamaが起動しているか確認してください。")
        print("")
        print(" 例:")
        print(" ollama serve")
        return None

    except requests.exceptions.RequestException as e:
        print("")
        print(" Ollamaとの通信中にエラーが発生しました。")
        print(f" {e}")
        return None


    if response.status_code == 200:

        try:
            result = response.json()

            return result["message"]["content"]

        except Exception as e:
            print("")
            print(" Ollamaからの応答を解析できませんでした。")
            print(f" {e}")
            return None

    else:

        print("")
        print(
            f" Error: {response.status_code}"
        )

        print(response.text)

        return None


# =========================================================
# メイン処理
# =========================================================

BOT_NAME=load_BotName()
def main():
    c=0

    try:
        print(pyfiglet.figlet_format("Velwether",font="slant"))
        print("Local AI Edition")
        c=1
    except:
        pass
    
    if c==0:
        print("")
        print(" ========================================")
        print("              Velwether")
        print("           Local AI Edition")
        print(" ========================================")
    print("")

    model = load_model()

    print(f" 使用モデル : {model}")
    print("")

    # -----------------------------------------------------
    # Ollama起動確認
    # -----------------------------------------------------

    print(" Ollamaとの接続を確認しています...")

    if not check_ollama():

        print("")
        print(" Ollamaに接続できませんでした。")
        print("")
        print(" Ollamaがインストールされているか確認してください。")
        print("")
        print(" PowerShellで次を実行してください。")
        print("")
        print(" ollama serve")
        print("")

        input(" >> ")

        sys.exit()

    print(" Ollama接続: OK")


    # -----------------------------------------------------
    # モデル確認
    # -----------------------------------------------------

    if not check_model():

        print("")
        print(
            f" モデル '{model}' がインストールされていません。"
        )
        print("")
        print(" PowerShellで次を実行してください。")
        print("")
        print(
            f" ollama pull {model}"
        )
        print("")

        input(" >> ")

        sys.exit()


    print(f" モデル確認: {model} OK")
    print("")


    # -----------------------------------------------------
    # 会話履歴
    # -----------------------------------------------------

    if load_preload() == 1:

        messages = load_chat()

        if os.path.isfile(CHAT_LOG_FILE):
            print(" 前回の会話履歴を読み込みました。")

    else:

        if os.path.isfile(CHAT_LOG_FILE):

            print("")
            v = input(
                " これまでの会話履歴を読み込みますか？ (Y/n) >> "
            )

            if v.lower() in ["", "y", "yes"]:
                messages = load_chat()

            else:
                messages = new_chat()

        else:
            messages = new_chat()


    # -----------------------------------------------------
    # 操作説明
    # -----------------------------------------------------

    print("")
    print(f" {BOT_NAME}に話しかけてみてください！")
    print("")
    print(" 終了       : exit")
    print(" 履歴削除   : clear")
    print(" 履歴表示   : history")
    print(" モデル表示 : model")
    print("")
    print(
        " 会話履歴はローカルのmemory.vlmに保存されます。"
    )
    print("")


    # -----------------------------------------------------
    # チャットループ
    # -----------------------------------------------------

    while True:

        try:

            user_input = input("\n あなた: ").strip()

        except KeyboardInterrupt:

            print("")
            print("")
            print(" 会話を終了します。")

            break


        # -------------------------------------------------
        # 空入力
        # -------------------------------------------------

        if not user_input:
            continue


        # -------------------------------------------------
        # 終了
        # -------------------------------------------------

        if user_input.lower() == "exit":

            print("")
            print(" 会話を終了します。")

            break


        # -------------------------------------------------
        # 履歴削除
        # -------------------------------------------------

        if user_input.lower() == "clear":

            messages = new_chat()

            if os.path.isfile(CHAT_LOG_FILE):

                try:
                    os.remove(CHAT_LOG_FILE)

                except Exception as e:
                    print(
                        f" 履歴削除エラー: {e}"
                    )

                    continue

            print("")
            print(" 会話履歴を削除しました。")

            continue


        # -------------------------------------------------
        # 履歴表示
        # -------------------------------------------------

        if user_input.lower() == "history":

            print("")
            print(" ===== 会話履歴 =====")

            for message in messages:

                role = message.get("role", "")
                content = message.get("content", "")

                if role == "system":
                    continue

                if role == "user":
                    print("")
                    print(f" あなた: {content}")

                elif role == "assistant":
                    print("")
                    print(f" ボット: {content}")

            print("")
            print(" ====================")

            continue


        # -------------------------------------------------
        # モデル情報
        # -------------------------------------------------

        if user_input.lower() == "model":

            print("")
            print(
                f" 使用中モデル: {load_model()}"
            )

            continue


        # -------------------------------------------------
        # ユーザーメッセージ追加
        # -------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )


        # -------------------------------------------------
        # Ollama呼び出し
        # -------------------------------------------------

        print("")
        print(" 考え中...")

        response = chat_with_ollama(messages)

        if response is None:

            # APIエラー時はユーザー入力を履歴から外す
            if (
                len(messages) > 0
                and messages[-1]["role"] == "user"
            ):
                messages.pop()

            continue


        # -------------------------------------------------
        # AI応答を履歴へ追加
        # -------------------------------------------------

        messages.append(
            {
                "role": "assistant",
                "content": response
            }
        )


        # -------------------------------------------------
        # 会話履歴保存
        # -------------------------------------------------

        save_chat(messages)


        # -------------------------------------------------
        # 表示
        # -------------------------------------------------

        display_response = response.replace(
            "。",
            "。\n "
        )
        
        display_response = response.replace(
                    "**",
                    ""
                )

        print("")
        print(
            f" {BOT_NAME}: {display_response}"
        )


# =========================================================
# 起動
# =========================================================

if __name__ == "__main__":
    main()