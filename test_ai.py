# test_ai.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load credentials
load_dotenv()
api_key = os.getenv("ZAI_API_KEY")
base_url = os.getenv("ZAI_BASE_URL")
model = os.getenv("ZAI_MODEL", "glm-5.1")

print(f"--- API 疎通テスト開始 ---")
print(f"Base URL: {base_url}")
print(f"Model: {model}")

# 2. Check key
if not api_key:
    print("エラー: ZAI_API_KEY が .env に設定されていません。")
    exit(1)

# 3. Call AI
client = OpenAI(api_key=api_key, base_url=base_url)

try:
    print("[*] AI にメッセージ送信中...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "こんにちは、聞こえますか？疎通確認です。"}
        ],
        max_tokens=50
    )
    print("\n--- AI からの応答（生データ） ---")
    print(response)
    print("\n--- 抽出された本文 ---")
    print(f"Content: '{response.choices[0].message.content}'")
    print("--------------------")
    if response.choices[0].message.content:
        print("[成功] AI との意思疎通に成功しました！")
    else:
        print("[警告] 通信は成功しましたが、返信内容が空です。モデルが非対応か、パラメータ調整が必要です。")

except Exception as e:
    print("\n--- エラー発生 ---")
    print(f"接続に失敗しました: {e}")
    print("------------------")
