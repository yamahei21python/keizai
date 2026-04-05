# summarize_report.py
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load credentials from .env
load_dotenv()

ZAI_API_KEY = os.getenv("ZAI_API_KEY")
ZAI_MODEL = os.getenv("ZAI_MODEL", "glm-5.1")
ZAI_BASE_URL = os.getenv("ZAI_BASE_URL")

# 2. Initialize OpenAI-compatible client for Z.ai
client = OpenAI(
    api_key=ZAI_API_KEY,
    base_url=ZAI_BASE_URL
)

def get_ai_summary(text):
    print(f"[*] Sending content to AI ({ZAI_MODEL})...")
    
    prompt = """
あなたはプロの投資アナリストです。以下の経済レポートの内容を精読し、投資家の意思決定に役立つ形で要約してください。

以下の形式で出力してください：
■ 3つの要点
・（要点1）
・（要点2）
・（要点3）

■ 投資判断への影響とリスク
・（市場や特定のセクター、通貨等への影響、および注目すべきリスク）
"""

    try:
        response = client.chat.completions.create(
            model=ZAI_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"以下のレポートを要約してください：\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: AI Summarization failed - {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 summarize_report.py <path_to_markdown_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    print(f"[*] Reading: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get summary
    summary = get_ai_summary(content)
    
    print("\n" + "="*50)
    print("AI SUMMARY RESULTS")
    print("="*50)
    print(summary)
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
