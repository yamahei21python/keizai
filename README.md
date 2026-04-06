# 経済インテリジェンス・パイプライン (Modernized) 🚀

このリポジトリは、マクロ経済レポートのランキング取得から、**Google NotebookLM** による高品質な AI 要約作成、そしてウェブダッシュボードへの公開までを完全自動化するシステムです。

## 🌟 コア・アーキテクチャ（一本の背骨）

断片化していたスクリプトを整理し、信頼性の高い一つのマスター・パイプラインへと統合しました：

1.  **Stage 1: スマート・スクレイピング** (`unified_pipeline.py` + `keizai_scraper.py`)
    - 最新のマクロ経済レポート（上位10件）を取得します。
    - WAFで保護されたジャンプURLを、ハイブリッド・プロキシ（ScraperAPI）で突破し、最終的なソースURLを特定します。
    - NotebookLM が読み込める形式（`Source: URL`付き）でメタデータを Markdown 化して保存します。
2.  **Stage 2: AI インテリジェンス** (`generate_individual_notebooks.py`)
    - ブラウザ自動操作 CLI を介して Google NotebookLM と連携します。
    - NotebookLM の標準機能である **「Briefing Doc」** を使い、プロレベルの要約を日本語で自動生成します。
    - 処理が終わったノートブックは自動削除され、クラウド上のストレージを常にクリーンに保ちます。
3.  **Stage 3: ウェブ同期** (`build_index.py`)
    - 保存された Markdown と要約データをスキャンし、`reports.json` を再構築します。
    - これにより、React ダッシュボード (`keizai-web`) が即座に最新状態に更新されます。

## 📂 プロジェクト構成

```text
keizai/
├── unified_pipeline.py       # 【メイン】これ一本ですべての工程を実行する司令塔。
├── keizai_scraper.py         # スクレイピングの心臓部（Playwright + Stealth）。
├── build_index.py            # ウェブ表示用インデックス生成（JSON 構築）。
├── keizai-web/               # フロントエンド（Vite/React ダッシュボード）。
└── notebooklm-podcast-lab/    # NotebookLM 操作用ラボ（別館）。
    └── generate_individual_notebooks.py # 要約生成のメインエンジン。
```

## 🛠 セットアップと実行

### **前提条件**
- Python 3.12+ / [uv](https://github.com/astral-sh/uv)
- Google Chrome インストール済み
- NotebookLM ログイン済み (`nlm login` 実行済み)

### **実行コマンド**
ターミナルで以下のコマンドを実行するだけです：
```bash
python3 unified_pipeline.py 10
```

## 🤖 自動化 (GitHub Actions)

このパイプラインは毎日定刻に GitHub 上で自動実行されます。
- **ワークフロー**: `.github/workflows/daily_keizai.yml`
- **必要な Secrets**:
    - `SCRAPERAPI_KEY`: WAF 突破用の API キー。
    - `NOTEBOOKLM_STORAGE_STATE`: ローカルの `~/.notebooklm/storage_state.json` の中身（認証情報の同期用）。

---
*Created by Antigravity AI*
