# Daily Keizai Intelligence Pipeline 🚀

経済レポートのランキング取得から、AI（NotebookLM）による要約作成、Webサイトへの公開までを自動化する統合システムです。

## 🌟 主な機能

- **全自動レポート収集**: `keizaireport.com` のランキングから、最新のレポート（PDF/HTML）を自動取得しMarkdown化。
- **NotebookLM 連携**: Google NotebookLM を活用し、プロレベルの「Briefing Doc（要約）」を自動生成。
- **スマート・スキップロジック**: 既に要約が存在する場合は、不要なフェッチ処理をスキップして効率化。
- **自動クリーンアップ**: 処理が終わった箇所のノートブックを随時削除し、作業スペースを常にクリーンに維持。
- **Web UI 連携**: 生成された要約を即座にポートフォリオサイト（`keizai-web`）へ反映。

## 📂 プロジェクト構成

```text
keizai/
├── run_daily_keizai.py       # 【メイン】一連の作業を実行するマスタースクリプト
├── unified_pipeline.py      # レポートの取得・保存処理（Phase 1）
├── build_index.py           # Web表示用のインデックス更新（Phase 3）
├── fetch_ranking.scpt       # AppleScript: ランキング情報の抽出
├── resolve_jump.scpt        # AppleScript: リダイレクト先の解決
├── capture_content.scpt     # AppleScript: 本文のキャプチャ
├── keizai-web/              # フロントエンドWebアプリケーション
└── notebooklm-podcast-lab/   # NotebookLM 操作用スクリプト群
    ├── generate_individual_notebooks.py  # 個別レポートの要約作成（Phase 2）
    ├── generate_consolidated_podcast.py  # 統合ポッドキャストの生成（オプション）
    └── cleanup_notebooks.py              # 不要なノートブックの一括削除
```

## 🛠 セットアップと実行

### **前提条件**
- macOS (AppleScript / Chrome 操作のため)
- Google Chrome インストール済み
- [uv](https://github.com/astral-sh/uv) (Python パッケージ管理ツール)
- NotebookLM CLI (uv経由で実行可能な環境)

### **実行方法**
ターミナルでリポジトリのルート（`keizai/`）に移動し、以下のコマンドを実行するだけです。

```bash
python3 run_daily_keizai.py
```

### **動作ロジック**
1. **重複チェック**: 今日の要約が既にあれば、レポート取得（Phase 1）をスキップします。
2. **ブラウザ起動**: Chromeが閉じていれば自動で起動します。
3. **ワークフロー**: 「レポート取得 → 要約作成 → インデックス更新」を順次実行します。
4. **自動削除**: 要約作成が成功すると、NotebookLM上のノートブックは即座に削除されます。

## 📝 メンテナンス

もしNotebookLM上に不要なノートブックが溜まってしまった場合は、以下のコマンドで一括削除できます。
```bash
cd notebooklm-podcast-lab
uv run python cleanup_notebooks.py
```

---
*Created by Antigravity (AI Coding Assistant)*
