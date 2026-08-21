import requests
import os
import sys
import configparser
import shutil
import pyfiglet
import traceback

# =========================================================
# 画面クリア
# =========================================================

os.system("cls" if os.name == "nt" else "clear")


import pyttsx3

def load_config():
    config = configparser.ConfigParser()

    with open(CONFIG_FILE, "r", encoding="utf-8") as configfile:
        config.read_file(configfile)

    return config

def load_DVDmode():
    """
    DVDモードの有効無効を変更
    """
    config = load_config()

    try:
        return int(config["DEFAULT"]["dvd_mode"])
    except KeyError:
        return 0  

def setup_dropbox_oauth():
    import dropbox

    config = load_dropbox_config()

    app_key = config["DROPBOX"]["app_key"].strip()

    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
        app_key,
        token_access_type="offline",
        use_pkce=True
    )

    authorize_url = auth_flow.start()

    import webbrowser

    webbrowser.open(authorize_url)

    auth_code = input(
        " 表示された認証コードを入力してください >> "
    ).strip()

    result = auth_flow.finish(auth_code)

    refresh_token = result.refresh_token

    config["DROPBOX"]["refresh_token"] = refresh_token

    with open(
        DROPBOX_CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        config.write(f)

    print("")
    print(" Dropbox認証が完了しました。")

    return refresh_token

def get_appdata_dir():
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "Velwether")
    os.makedirs(folder, exist_ok=True)
    return folder

# =========================================================
# 定数
# =========================================================

APP_DATA=get_appdata_dir()
CONFIG_DIR = "config"
DATA_DIR = "data"
LOG_DIR ="logs"

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")
if load_DVDmode()==0:
    DROPBOX_CONFIG_FILE = os.path.join(CONFIG_DIR, "dropbox.ini")
    CHAT_LOG_FILE = os.path.join(DATA_DIR, "memory.vlm")
    LOG_FILE = os.path.join(LOG_DIR, "message.log")
else:
    
    LOG_FILE = os.path.join(APP_DATA, "message.log")
    CHAT_LOG_FILE = os.path.join(APP_DATA, "memory.vlm")
    if os.path.isfile(os.path.join(CONFIG_DIR, "dropbox.ini")) and not os.path.isfile(os.path.join(APP_DATA, "dropbox.ini")):
        shutil.copyfile(
            os.path.join(CONFIG_DIR, "dropbox.ini"),
            os.path.join(APP_DATA, "dropbox.ini")
        )

    if (os.path.isfile(os.path.join(CONFIG_DIR, "config.ini")) and not os.path.isfile(os.path.join(APP_DATA, "config.ini"))):
        shutil.copyfile(
            os.path.join(CONFIG_DIR, "config.ini"),
            os.path.join(APP_DATA, "config.ini")
            )
    DROPBOX_CONFIG_FILE = os.path.join(APP_DATA, "dropbox.ini")
    CONFIG_FILE = os.path.join(APP_DATA, "config.ini")


os.makedirs(CONFIG_DIR, exist_ok=True)
if load_DVDmode()==0:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

# =========================================================
# 設定データなどの移行
# =========================================================


if os.path.isfile("config.ini"):
    shutil.copyfile("config.ini",CONFIG_FILE)
    os.remove("config.ini")
    print("設定データを移行しました。")

if os.path.isfile("memory.vlm"):
    i=input(" 既存の記憶データを移行しますか? ( Y or N ) >> ")
    if i.lower()=="y":
        if os.path.isfile(CHAT_LOG_FILE):
            print("")
            d=input(" 記憶データが既に存在します。上書きしますか? ( Y or N ) >> ")
            if d.lower()=="y":
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

def load_voice():
    """
    合成音声の有効無効を変更
    """
    config = load_config()

    try:
        return int(config["DEFAULT"]["voice_enable"])
    except KeyError:
        return 0

def load_log():
    """
    ログの有効無効を変更
    """
    config = load_config()

    try:
        return int(config["DEFAULT"]["log_enable"])
    except KeyError:
        return 0

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

LOG_ENABLD=load_log()
VOICE_ENABLD=load_voice()
# ========================================================
## ログ出力
#========================================================
def write_log(messages):
    if LOG_ENABLD==0:
        return 
    import json

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n--- messages[-3:] ---\n")
        f.write(json.dumps(messages[-3:], ensure_ascii=False, indent=2))
        f.write("\n")

#========================================================
# ボイス設定
#========================================================

if VOICE_ENABLD==1:
    engine = pyttsx3.init()

    voices = engine.getProperty("voices")

    engine.setProperty("voice", voices[0].id)

# =========================================================
# Dropbox設定 / 記憶同期
# =========================================================

def load_dropbox_config():
    """
    config/dropbox.ini を読み込む。
    ファイルが無い場合はDropbox同期を無効として扱う。
    """
    config = configparser.ConfigParser()

    if not os.path.isfile(DROPBOX_CONFIG_FILE):
        return config

    with open(DROPBOX_CONFIG_FILE, "r", encoding="utf-8") as configfile:
        config.read_file(configfile)

    return config


def load_dropbox_enabled():
    config = load_dropbox_config()

    try:
        return config["DROPBOX"].getboolean("enabled")
    except (KeyError, ValueError):
        return False


def load_dropbox_memory_path():
    config = load_dropbox_config()

    try:
        path = config["DROPBOX"]["memory_path"].strip()
        return path if path else "/Velwether/memory.vlm"
    except KeyError:
        return "/Velwether/memory.vlm"

def get_dropbox_client():
    import dropbox

    config = load_dropbox_config()

    try:
        app_key = config["DROPBOX"]["app_key"].strip()
    except KeyError:
        app_key = ""

    try:
        refresh_token = config["DROPBOX"]["refresh_token"].strip()
    except KeyError:
        refresh_token = ""

    if not app_key:
        print("")
        print(" Dropbox App Keyが設定されていません。")
        app_key = input(
            " Dropbox App Keyを入力してください >> "
        ).strip()

        if not app_key:
            raise RuntimeError(
                "Dropbox App Keyが入力されませんでした。"
            )

        if "DROPBOX" not in config:
            config["DROPBOX"] = {}

        config["DROPBOX"]["app_key"] = app_key

        with open(
            DROPBOX_CONFIG_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            config.write(f)

        print("")
        print(" Dropbox App Keyを保存しました。")

    if not refresh_token:
        refresh_token = setup_dropbox_oauth()

    return dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key
    )


def ensure_dropbox_parent(dbx, remote_path):
    """
    /Velwether/memory.vlm のような保存先について、
    必要な親フォルダをDropbox側に作成する。
    """
    normalized = remote_path.replace("\\", "/")

    if not normalized.startswith("/"):
        normalized = "/" + normalized

    parts = [part for part in normalized.split("/") if part]

    # 最後はファイル名なので除外
    if len(parts) <= 1:
        return

    current = ""

    for part in parts[:-1]:
        current += "/" + part

        try:
            dbx.files_create_folder_v2(current)
        except Exception:
            # 既存フォルダの場合などはそのまま続行
            pass


def _to_utc(dt):
    """
    Dropbox SDKが返すnaive datetimeをUTCとして正規化する。
    """
    from datetime import timezone

    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def get_local_memory_modified():
    if not os.path.isfile(CHAT_LOG_FILE):
        return None

    from datetime import datetime, timezone

    return datetime.fromtimestamp(
        os.path.getmtime(CHAT_LOG_FILE),
        tz=timezone.utc
    )


def get_dropbox_memory_metadata(dbx):
    try:
        return dbx.files_get_metadata(
            load_dropbox_memory_path()
        )
    except Exception:
        return None


def upload_memory_to_dropbox(show_error=False):
    """
    ローカルのmemory.vlmをDropboxへ上書きアップロードする。
    失敗してもローカル保存は維持する。
    """
    if not load_dropbox_enabled():
        return False

    if not os.path.isfile(CHAT_LOG_FILE):
        return False

    try:
        import dropbox

        dbx = get_dropbox_client()
        remote_path = load_dropbox_memory_path()

        ensure_dropbox_parent(dbx, remote_path)

        local_modified = get_local_memory_modified()

        with open(CHAT_LOG_FILE, "rb") as f:
            dbx.files_upload(
                f.read(),
                remote_path,
                mode=dropbox.files.WriteMode.overwrite,
                client_modified=(
                    local_modified.replace(tzinfo=None)
                    if local_modified is not None
                    else None
                ),
                mute=True
            )

        return True

    except Exception as e:
        if show_error:
            
            print("")
            print(" Dropboxへの記憶データ同期に失敗しました。")
            print(f" {type(e).__name__}: {e}")
            traceback.print_exc()

        return False


def download_memory_from_dropbox(dbx, metadata):
    """
    Dropboxのmemory.vlmを一時ファイルへ取得し、
    JSONとして読めることを確認してからローカルを置換する。
    """
    import json

    remote_path = load_dropbox_memory_path()
    temp_file = CHAT_LOG_FILE + ".tmp"

    _, response = dbx.files_download(remote_path)

    # Dropboxから取得した内容を一時保存
    with open(temp_file, "wb") as f:
        f.write(response.content)

    try:
        # 壊れたデータでローカル記憶を上書きしない
        with open(temp_file, "r", encoding="utf-8") as f:
            test_messages = json.load(f)

        if not isinstance(test_messages, list):
            raise ValueError(
                "Dropbox上のmemory.vlmの形式が正しくありません。"
            )

        # 最低限、各要素が辞書かも確認
        for message in test_messages:
            if not isinstance(message, dict):
                raise ValueError(
                    "Dropbox上のmemory.vlmのメッセージ形式が正しくありません。"
                )

        os.replace(temp_file, CHAT_LOG_FILE)

    except Exception:
        # 検証失敗時はtmpを残さない
        if os.path.isfile(temp_file):
            os.remove(temp_file)
        raise

    remote_modified = _to_utc(
        getattr(metadata, "client_modified", None)
    )

    if remote_modified is not None:
        timestamp = remote_modified.timestamp()
        os.utime(CHAT_LOG_FILE, (timestamp, timestamp))


def sync_memory():
    """
    起動時にローカルとDropboxのmemory.vlmを比較する。

    Dropboxが新しい:
        Dropbox -> ローカル
    ローカルが新しい:
        ローカル -> Dropbox
    片方だけ存在:
        存在する側をもう片方へ同期

    ネット未接続などでDropboxへ接続できない場合は
    ローカルだけでそのまま起動する。
    """
    if not load_dropbox_enabled():
        return

    try:
        dbx = get_dropbox_client()

        local_modified = get_local_memory_modified()
        remote_metadata = get_dropbox_memory_metadata(dbx)

        remote_modified = None

        if remote_metadata is not None:
            remote_modified = _to_utc(
                getattr(remote_metadata, "client_modified", None)
            )

        # 両方ない
        if local_modified is None and remote_metadata is None:
            return

        # Dropboxだけある
        if local_modified is None and remote_metadata is not None:
            print(" Dropboxから記憶データを取得しています...")
            download_memory_from_dropbox(dbx, remote_metadata)
            print(" Dropboxの記憶データを取得しました。")
            return

        # ローカルだけある
        if local_modified is not None and remote_metadata is None:
            print(" ローカルの記憶データをDropboxへ同期しています...")
            if upload_memory_to_dropbox(show_error=True):
                print(" Dropboxへの同期が完了しました。")
            return

        # 更新日時が取れない場合はローカル優先
        if remote_modified is None:
            upload_memory_to_dropbox(show_error=True)
            return

        # Dropboxの方が新しい
        if remote_modified > local_modified:
            print(" Dropboxに新しい記憶データがあります。")
            download_memory_from_dropbox(dbx, remote_metadata)
            print(" Dropboxの記憶データを使用します。")

        # ローカルの方が新しい
        elif local_modified > remote_modified:
            print(" ローカルの記憶データの方が新しいためDropboxへ同期します。")
            upload_memory_to_dropbox(show_error=True)

        else:
            print(" Dropboxとの記憶データは同期済みです。")

    except Exception as e:
        print("")
        print(" Dropboxに接続できないためローカルの記憶データを使用します。")
        print(f" {e}")


# =========================================================
# 会話履歴
# =========================================================

def save_chat(messages):
    """
    会話履歴全体をmemory.vlmへJSON形式で保存する。
    Dropbox同期が有効なら、ローカル保存後にクラウドへ同期する。
    """
    import json

    try:
        with open(CHAT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(
                messages,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:
        print("")
        print(" 会話履歴の保存中にエラーが発生しました。")
        print(f" {e}")
        return

    upload_memory_to_dropbox(show_error=False)


def load_chat():
    """
    memory.vlmからJSON形式の会話履歴を読み込む
    """
    import json

    if not os.path.isfile(CHAT_LOG_FILE):
        return [
            {
                "role": "system",
                "content": load_system_prompt()
            }
        ]

    try:
        with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)

        if not isinstance(messages, list):
            raise ValueError(
                "memory.vlmの形式が正しくありません。"
            )

        for message in messages:
            if not isinstance(message, dict):
                raise ValueError(
                    "memory.vlmのメッセージ形式が正しくありません。"
                )

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
            "num_predict": load_token(),
            "temperature": 0.8,
            "repeat_penalty": 1.15
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
DVD_MODE = load_DVDmode()
BOT_NAME = load_BotName()
def main():
    c=0

    try:
        print(pyfiglet.figlet_format("Velwether",font="slant"))
        print("Local AI Edition")
        if DVD_MODE == 1:
            print("For DVD Mode")
        print("")
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
    # Dropbox記憶同期
    # -----------------------------------------------------

    sync_memory()

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
        " 会話履歴は data/memory.vlm に保存され、Dropbox同期が有効な場合はクラウドにも保存されます。"
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

            # 空の会話履歴を保存してDropbox側にも反映する。
            # ローカルだけ削除すると次回起動時にDropboxから
            # 古い履歴が復元されてしまうため。
            save_chat(messages)

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
                    print(f" {BOT_NAME}: {content}")

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

        write_log(messages) # 会話履歴の生データを保存

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
        
        display_response = display_response.replace(
                    "**",
                    ""
                )

        print("")
        print(
            f" {BOT_NAME}: {display_response}"
        )
        if VOICE_ENABLD==1:
            engine.say(display_response)
            engine.runAndWait()


# =========================================================
# 起動
# =========================================================

if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit(0)