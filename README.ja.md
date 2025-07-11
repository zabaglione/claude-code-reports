# Claude Code Report Generator

Claude Codeとの会話履歴を分析し、プロジェクト別・期間別のサマリーレポートを生成するCLIツールです。

## 概要

このツールは、Claude Codeの会話履歴（JSONLファイル）を解析し、以下の情報を含むMarkdownレポートを生成します：

- プロジェクト別の活動サマリー
- ツール使用統計
- 日別・時間帯別のアクティビティ分析
- 会話内容の要約（画像やファイル操作を含む）

## 特徴

- 📊 **詳細な統計情報**: プロジェクト毎のセッション数、メッセージ数、期間を集計
- 🔧 **ツール使用分析**: Read, Write, Edit, Bash, WebFetch等の使用頻度を分析
- 📅 **柔軟な期間指定**: 日数指定または開始・終了日を直接指定可能
- 🎯 **スマートな要約**: 画像ファイル、コード実装依頼、エラー修正等を自動分類
- 🌐 **多言語対応**: システムロケールに基づく自動言語検出（英語/日本語）
- 🚀 **高速処理**: Python標準ライブラリのみ使用、外部依存なし

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/zabaglione/claude-code-reports.git
cd claude-code-reports

# 実行権限の付加
chmod +x claude_report.py
```

## 使い方

### 基本的な使用方法

```bash
# 過去7日間のレポートを生成（デフォルト）
python3 claude_report.py

# 過去30日間のレポートを生成
python3 claude_report.py --days 30

# 特定の期間を指定
python3 claude_report.py --from 2025-07-01 --to 2025-07-05

# 特定のプロジェクトのみを対象
python3 claude_report.py --project myproject

# ファイルに保存
python3 claude_report.py -o report.md

# 日本語出力を強制
python3 claude_report.py --lang ja

# 英語出力を強制
python3 claude_report.py --lang en
```

### 言語の自動検出

ツールは`LANG`環境変数からシステムの言語を自動検出します：
- 日本語（`ja_JP`等）→ 日本語出力
- その他 → 英語出力（デフォルト）

`--lang`オプションで手動指定することも可能です。

### コマンドラインオプション

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `--days` | 過去何日分のデータを分析するか | 7 |
| `--from` | 開始日（YYYY-MM-DD形式） | - |
| `--to` | 終了日（YYYY-MM-DD形式） | - |
| `--project` | 特定のプロジェクト名でフィルタ | - |
| `--output`, `-o` | レポートの出力先ファイル | 標準出力 |
| `--lang` | 出力言語（en/ja） | 自動検出 |

## レポートの内容

生成されるレポートには以下の情報が含まれます：

### プロジェクト別サマリー
- セッション数とメッセージ数
- 活動期間（最初と最後のアクティビティ）
- 主な話題（自動要約）
  - 画像ファイルの処理
  - コード実装依頼
  - エラー修正・デバッグ
  - ファイル操作（作成/編集/確認）
  - Web参照
- ツール使用回数（上位5つ）

### 全体統計
- ツール使用統計（全プロジェクト合計）
- 日別アクティビティ
- 時間帯別アクティビティ（視覚的なバーグラフ付き）

## 必要な環境

- Python 3.6以上
- Claude Codeの会話履歴ディレクトリ（`~/.claude/projects/`）

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します。大きな変更を行う場合は、まずイシューを作成して変更内容について議論してください。

## 作者

z_zabaglione ([@z_zabaglione](https://x.com/z_zabaglione))