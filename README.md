# Velwether - Local AI Edition

Velwether Local AI Edition は、Ollamaを利用してローカル環境でAIモデルと会話するためのCLIチャットアプリです。

OpenAI APIなどの外部AI APIを必須とせず、Ollama上にインストールしたモデルを利用して会話できます。

## 主な機能

- Ollama上のローカルAIモデルとのチャット
- 使用モデルを `config/config.ini` から変更可能
- ボット名を設定可能
- System Prompt による人格・応答スタイル設定
- 会話履歴の保存・読み込み
- 起動時の履歴自動読み込み設定
- 会話履歴の削除・表示
- 使用中モデルの確認
- FIGletによる起動ロゴ表示
- Ollamaサーバーおよびモデルの存在確認
- Dropboxへの記憶データ同期（対応版のみ）
- ネットワーク未接続時もローカルの記憶データを利用可能

## 必要環境

- Windows 10 / 11
- Python 3
- Ollama
- 使用するOllamaモデル

```powershell
pip install requests pyfiglet
```

Dropbox同期を利用する場合:

```powershell
pip install dropbox
```

## Ollamaの準備

```powershell
ollama pull qwen3:1.7b
```

必要に応じて:

```powershell
ollama serve
```

## ディレクトリ構成

```text
Velwether/
├─ Velwether.py
├─ config/
│  ├─ config.ini
│  └─ dropbox.ini
└─ data/
   └─ memory.vlm
```

## config.ini

```ini
[DEFAULT]
model = qwen3:1.7b
ollama_url = http://localhost:11434/api/chat
bot_name = ゆらら
preload = 1
Max_Token = 1024
system_prompt = あなたは自然な日本語で会話するAIです。回答は要点だけを簡潔に述べてください。通常の回答は2〜4行程度にしてください。不要な前置きや長い解説は避け、詳しい説明を求められた場合のみ詳細に答えてください。Markdown記法は使用しないでください。
```

## Dropbox同期

Dropbox同期対応版では、会話履歴をローカルの `data/memory.vlm` に保存したうえでDropboxにも同期できます。

`config/dropbox.ini`:

```ini
[DROPBOX]
enabled = true
access_token = YOUR_DROPBOX_ACCESS_TOKEN
memory_path = /AI Memory/memory.vlm
```

> [!IMPORTANT]
> `config.ini` や `dropbox.ini` にAPIキー・アクセストークンなどの秘密情報を保存する場合は、Gitへコミットしないでください。

`.gitignore` 例:

```gitignore
config/config.ini
config/dropbox.ini
data/memory.vlm
```

## 起動

```powershell
python Velwether.py
```

## コマンド

| コマンド | 内容 |
| --- | --- |
| `exit` | Velwetherを終了 |
| `clear` | 会話履歴を削除 |
| `history` | 現在の会話履歴を表示 |
| `model` | 使用中のOllamaモデルを表示 |

## 会話履歴

会話履歴は `data/memory.vlm` に保存されます。

`memory.vlm` はPythonのpickle形式を利用したバイナリデータです。通常のテキストエディタで開くことは想定していません。

## 注意事項

- AIの回答内容は使用するOllamaモデルによって大きく異なります。
- 小型モデルでは日本語表現や指示追従が不安定になる場合があります。
- モデルが大きいほど、一般的により多くのRAMとCPU/GPU性能が必要です。
- VelwetherはOllama本体やAIモデルを同梱していません。
- Dropboxアクセストークンなどの秘密情報を公開リポジトリへ含めないでください。

## License

This project is licensed under the MIT License.

See `LICENSE` for details.
