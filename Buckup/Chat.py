import requests
import os
import sys

os.system("cls")

if os.path.isfile("config.ini")==False:
    print(" config.iniファイルが見つかりません。")
    input(" >> ")
    sys.exit()

def load_config():
    import configparser

    config = configparser.ConfigParser()

    # 'config.ini' をUTF-8として読み込む
    with open('config.ini', 'r', encoding='utf-8') as configfile:
        config.read_file(configfile)

    # デフォルトのAPIキーを取得
    default_api_key = config['DEFAULT']['api_key']

    return default_api_key

def load_config1():
    import configparser

    config = configparser.ConfigParser()

    # 'config.ini' をUTF-8として読み込む
    with open('config.ini', 'r', encoding='utf-8') as configfile:
        config.read_file(configfile)

    # config.iniファイルの読み込み
    config.read('config.ini')

    # プレクリアフラグを取得
    precls = config['DEFAULT']['pre_cls']

    return precls

def load_Token():
    import configparser

    config = configparser.ConfigParser()

    # 'config.ini' をUTF-8として読み込む
    with open('config.ini', 'r', encoding='utf-8') as configfile:
        config.read_file(configfile)

    # config.iniファイルの読み込み
    config.read('config.ini')

    # プレクリアフラグを取得
    precls = config['DEFAULT']['Max_Token']

    return int(precls)

API_KEY = load_config()
API_URL = 'https://api.openai.com/v1/chat/completions'

def chat_with_gpt(prompt):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': load_Token()
    }

    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 429:
        print(" Error 429: エラーが発生しました。エラー情報は次の通りです。")
        print(" このエラーメッセージは、お客様がAPIの月間最大使用量（ハードリミット）に達したことを示します。\nこれは、お客様のプランに割り当てられたクレジットまたはユニットをすべて消費し、課金サイクルの限界に達したことを意味します。")
        print("\n 可能であるならば、APIキー管理アカウントにクレジットを追加してソフトウェアを再起動してください。")
        input(" >> ")
        sys.exit()
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def main():
    print("")
    print(" ボットに話しかけてみてください！\n 終了するには 'exit' と入力してください。")
    
    while True:
        user_input = input("\n あなた: ")
        if user_input.lower() == 'exit':
            print("会話を終了します。")
            break

        response = chat_with_gpt(user_input)
        response=response.replace("。","。\n")
        if response:
            print(f"\n ボット: {response}")

if __name__ == "__main__":
    main()
