#!/usr/bin/env python3
"""
Claude Code 会話履歴レポート生成ツール

Claude Codeとの会話履歴を分析し、プロジェクト別・期間別のサマリーレポートを生成します。
"""

import argparse
import json
import os
import sys
import re
import locale
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter


# 多言語対応のメッセージ辞書
MESSAGES = {
    'en': {
        'report_title': 'Claude Code Conversation History Report',
        'generated_at': 'Generated at',
        'total_sessions': 'Total sessions',
        'active_projects': 'Active projects',
        'project_summary': 'Project Summary',
        'sessions': 'Sessions',
        'messages': 'Messages',
        'period': 'Period',
        'main_topics': 'Main topics',
        'tools_used': 'Tools used',
        'tool_stats_overall': 'Tool Usage Statistics (Overall)',
        'daily_activity': 'Daily Activity',
        'hourly_activity': 'Hourly Activity',
        'times': 'times',
        'items': 'items',
        'image_file': 'Image file',
        'image_data': 'Image data processing',
        'screenshot': 'Screenshot analysis',
        'file_create': 'File creation',
        'file_edit': 'File edit',
        'file_read': 'File read',
        'file_operation': 'File operation',
        'web_reference': 'Web reference',
        'code_implementation': 'Code implementation request',
        'error_fix': 'Error fix/Debug',
        'code_related': 'Code related work',
        'loading_data': 'Loading data... (Period: {} to {})',
        'analyzing_data': 'Analyzing data...',
        'generating_report': 'Generating report...',
        'report_saved': 'Report saved to {}',
        'error': 'Error',
        'command_execution': 'command execution'
    },
    'ja': {
        'report_title': 'Claude Code 会話履歴レポート',
        'generated_at': '生成日時',
        'total_sessions': '総セッション数',
        'active_projects': 'アクティブプロジェクト数',
        'project_summary': 'プロジェクト別サマリー',
        'sessions': 'セッション数',
        'messages': 'メッセージ数',
        'period': '期間',
        'main_topics': '主な話題',
        'tools_used': '使用ツール',
        'tool_stats_overall': 'ツール使用統計（全体）',
        'daily_activity': '日別アクティビティ',
        'hourly_activity': '時間帯別アクティビティ',
        'times': '回',
        'items': '件',
        'image_file': '画像ファイル',
        'image_data': '画像データの処理',
        'screenshot': 'スクリーンショットの解析',
        'file_create': 'ファイル作成',
        'file_edit': 'ファイル編集',
        'file_read': 'ファイル確認',
        'file_operation': 'ファイル操作',
        'web_reference': 'Web参照',
        'code_implementation': 'コード実装依頼',
        'error_fix': 'エラー修正・デバッグ',
        'code_related': 'コード関連の作業',
        'loading_data': 'データを読み込み中... (期間: {} 〜 {})',
        'analyzing_data': 'データを分析中...',
        'generating_report': 'レポートを生成中...',
        'report_saved': 'レポートを {} に保存しました',
        'error': 'エラー',
        'command_execution': 'コマンド実行'
    }
}


def get_language(lang_override=None):
    """言語設定を取得（デフォルトは英語、日本語に対応）"""
    if lang_override:
        return 'ja' if lang_override.lower() == 'ja' else 'en'
    
    # LANG環境変数をチェック
    lang_env = os.environ.get('LANG', '').lower()
    if 'ja' in lang_env or 'jp' in lang_env:
        return 'ja'
    return 'en'


class ClaudeReportGenerator:
    """Claude Codeの会話履歴を分析しレポートを生成するクラス"""
    
    def __init__(self, base_path: str = "/Users/zabaglione/.claude/projects", language: str = 'en'):
        self.base_path = Path(base_path)
        self.sessions = []
        self.language = language
        self.msg = MESSAGES[language]
        
    def load_sessions(self, from_date: datetime, to_date: datetime, project_filter: Optional[str] = None) -> None:
        """指定期間のセッションデータを読み込む"""
        if not self.base_path.exists():
            raise FileNotFoundError(f"Claude projects directory not found: {self.base_path}")
            
        for project_dir in self.base_path.iterdir():
            if not project_dir.is_dir():
                continue
                
            # プロジェクト名を取得（ディレクトリ名から）
            project_name = project_dir.name.replace("-Users-zabaglione-", "")
            
            # プロジェクトフィルターの適用
            if project_filter and project_filter.lower() not in project_name.lower():
                continue
                
            # JSONLファイルを読み込む
            for jsonl_file in project_dir.glob("*.jsonl"):
                try:
                    session_data = self._load_jsonl_file(jsonl_file, from_date, to_date)
                    if session_data:
                        self.sessions.append({
                            "project": project_name,
                            "session_id": jsonl_file.stem,
                            "data": session_data
                        })
                except Exception as e:
                    print(f"Warning: Failed to load {jsonl_file}: {e}", file=sys.stderr)
                    
    def _load_jsonl_file(self, file_path: Path, from_date: datetime, to_date: datetime) -> List[Dict]:
        """JSONLファイルを読み込み、期間でフィルタリング"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if 'timestamp' in entry:
                        timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                        if from_date <= timestamp <= to_date:
                            data.append(entry)
                    else:
                        # タイムスタンプがないエントリも含める（summaryなど）
                        data.append(entry)
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue
        return data
        
    def _summarize_content(self, content: str) -> Optional[str]:
        """コンテンツを要約して返す"""
        if not content:
            return None
            
        # 改行とスペースを正規化
        content = re.sub(r'\s+', ' ', content).strip()
        
        # 画像ファイルパスの検出
        image_pattern = r'(?:^|\s|/)([^/\s]+\.(?:png|jpg|jpeg|gif|bmp|svg|webp))\b'
        image_match = re.search(image_pattern, content, re.IGNORECASE)
        if image_match:
            filename = image_match.group(1)
            return f"{self.msg['image_file']}: {filename}"
            
        # Base64データの検出
        if 'data:image' in content or (len(content) > 1000 and re.match(r'^[A-Za-z0-9+/\s]+={0,2}$', content)):
            return self.msg['image_data']
            
        # スクリーンショットパスの検出
        if 'screenshot' in content.lower() or 'screencapture' in content.lower():
            return self.msg['screenshot']
            
        # ファイルパスの検出（Read/Write系の操作）
        file_path_match = re.search(r'(?:^|\s)(/[\w\-./]+\.\w+)', content)
        if file_path_match:
            filepath = file_path_match.group(1)
            filename = os.path.basename(filepath)
            
            # ファイル操作の種類を判定
            if '作成' in content or 'create' in content.lower() or '生成' in content:
                return f"{self.msg['file_create']}: {filename}"
            elif '編集' in content or 'edit' in content.lower() or '修正' in content:
                return f"{self.msg['file_edit']}: {filename}"
            elif '読み' in content or 'read' in content.lower() or '確認' in content:
                return f"{self.msg['file_read']}: {filename}"
            else:
                return f"{self.msg['file_operation']}: {filename}"
                
        # URLの検出
        url_match = re.search(r'https?://[^\s]+', content)
        if url_match:
            url = url_match.group(0)
            domain = re.search(r'https?://([^/]+)', url)
            if domain:
                return f"{self.msg['web_reference']}: {domain.group(1)}"
                
        # コード記述依頼の検出
        code_keywords = ['実装', 'コード', 'プログラム', '関数', 'クラス', 'メソッド', 
                        'implement', 'code', 'function', 'class', 'method']
        for keyword in code_keywords:
            if keyword in content.lower():
                # より具体的な内容を抽出
                if '作成' in content or '作って' in content or 'create' in content.lower():
                    return self.msg['code_implementation']
                elif 'エラー' in content or 'error' in content.lower() or '修正' in content:
                    return self.msg['error_fix']
                else:
                    return self.msg['code_related']
                    
        # その他の一般的なトピック
        if len(content) > 100:
            # 長いコンテンツは最初の部分を抽出
            words = content.split()
            summary = ' '.join(words[:10])
            return summary[:50] + "..."
        else:
            return content[:50] + "..." if len(content) > 50 else content
            
    def _summarize_tool_use(self, tool_name: str, tool_input: Dict) -> Optional[str]:
        """ツール使用を要約して返す"""
        if tool_name == "Read":
            file_path = tool_input.get("file_path", "")
            if file_path:
                filename = os.path.basename(file_path)
                return f"[{tool_name}] {filename}"
                
        elif tool_name == "Write" or tool_name == "Edit":
            file_path = tool_input.get("file_path", "")
            if file_path:
                filename = os.path.basename(file_path)
                return f"[{tool_name}] {filename}"
                
        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            if command:
                # コマンドの最初の部分を抽出
                cmd_parts = command.split()
                if cmd_parts:
                    cmd_name = cmd_parts[0]
                    return f"[{tool_name}] {cmd_name} {self.msg['command_execution']}"
                    
        elif tool_name == "WebSearch":
            query = tool_input.get("query", "")
            if query:
                query_short = query[:30] + "..." if len(query) > 30 else query
                return f"[{tool_name}] {query_short}"
                
        elif tool_name == "WebFetch":
            url = tool_input.get("url", "")
            if url:
                domain = re.search(r'https?://([^/]+)', url)
                if domain:
                    return f"[{tool_name}] {domain.group(1)}"
                    
        return None
        
    def analyze_sessions(self) -> Dict:
        """セッションデータを分析"""
        analysis = {
            "total_sessions": len(self.sessions),
            "projects": defaultdict(lambda: {
                "sessions": [],
                "message_count": 0,
                "tool_usage": Counter(),
                "first_activity": None,
                "last_activity": None,
                "topics": []
            }),
            "tool_usage_overall": Counter(),
            "daily_activity": defaultdict(int),
            "hourly_activity": defaultdict(int)
        }
        
        for session in self.sessions:
            project_name = session["project"]
            project_data = analysis["projects"][project_name]
            project_data["sessions"].append(session["session_id"])
            
            for entry in session["data"]:
                # タイムスタンプの処理
                if 'timestamp' in entry:
                    # UTCタイムスタンプを読み込み
                    timestamp_utc = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    
                    # システムのローカルタイムゾーンに変換
                    timestamp_local = timestamp_utc.astimezone()
                    
                    # 最初と最後のアクティビティを記録（UTC時刻で保存）
                    if project_data["first_activity"] is None or timestamp_utc < project_data["first_activity"]:
                        project_data["first_activity"] = timestamp_utc
                    if project_data["last_activity"] is None or timestamp_utc > project_data["last_activity"]:
                        project_data["last_activity"] = timestamp_utc
                        
                    # 日別・時間別アクティビティ（ローカル時刻で集計）
                    analysis["daily_activity"][timestamp_local.date()] += 1
                    analysis["hourly_activity"][timestamp_local.hour] += 1
                
                # メッセージとツール使用の分析
                if entry.get("type") == "user" and "message" in entry:
                    project_data["message_count"] += 1
                    # 最初のユーザーメッセージをトピックとして記録
                    message = entry.get("message", {})
                    content = ""
                    
                    # メッセージ内容の取得（文字列またはリスト形式に対応）
                    if isinstance(message, dict):
                        msg_content = message.get("content", "")
                        if isinstance(msg_content, str):
                            content = msg_content
                        elif isinstance(msg_content, list):
                            # リスト形式の場合、テキストコンテンツを結合
                            text_parts = []
                            for item in msg_content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    text_parts.append(item.get("text", ""))
                                elif isinstance(item, str):
                                    text_parts.append(item)
                            content = " ".join(text_parts)
                    
                    if content and len(project_data["topics"]) < 3:
                        # コンテンツを要約
                        topic = self._summarize_content(content)
                        if topic:
                            project_data["topics"].append(topic)
                        
                elif entry.get("type") == "assistant" and "message" in entry:
                    # ツール使用の分析
                    message = entry.get("message", {})
                    if isinstance(message, dict) and "content" in message:
                        for content_item in message.get("content", []):
                            if isinstance(content_item, dict) and content_item.get("type") == "tool_use":
                                tool_name = content_item.get("name", "unknown")
                                project_data["tool_usage"][tool_name] += 1
                                analysis["tool_usage_overall"][tool_name] += 1
                                
                                # ツール使用の詳細をトピックに追加（最初の5個まで）
                                if len(project_data["topics"]) < 5:
                                    tool_summary = self._summarize_tool_use(tool_name, content_item.get("input", {}))
                                    if tool_summary:
                                        project_data["topics"].append(tool_summary)
                                
                # summaryタイプの処理
                elif entry.get("type") == "summary":
                    if "summary" in entry and len(project_data["topics"]) == 0:
                        project_data["topics"].append(entry["summary"])
                        
        return analysis
        
    def generate_markdown_report(self, analysis: Dict) -> str:
        """分析結果からMarkdownレポートを生成"""
        report = []
        
        # ヘッダー
        report.append(f"# {self.msg['report_title']}")
        
        # 日付フォーマットを言語に応じて変更
        if self.language == 'ja':
            date_format = '%Y年%m月%d日 %H:%M:%S'
        else:
            date_format = '%Y-%m-%d %H:%M:%S'
        
        report.append(f"\n{self.msg['generated_at']}: {datetime.now().strftime(date_format)}")
        
        # アクティブなプロジェクト数をカウント
        active_projects = sum(1 for p in analysis["projects"].values() 
                            if p["sessions"] and p["first_activity"] and p["last_activity"])
        
        report.append(f"{self.msg['total_sessions']}: {analysis['total_sessions']}")
        report.append(f"{self.msg['active_projects']}: {active_projects}")
        report.append("")
        
        # プロジェクト別サマリー
        report.append(f"## {self.msg['project_summary']}")
        report.append("")
        
        for project_name, project_data in sorted(analysis["projects"].items()):
            if not project_data["sessions"]:
                continue
            
            # タイムスタンプがないプロジェクトはスキップ
            if not project_data["first_activity"] or not project_data["last_activity"]:
                continue
                
            report.append(f"### 📁 {project_name}")
            report.append(f"- {self.msg['sessions']}: {len(project_data['sessions'])}")
            report.append(f"- {self.msg['messages']}: {project_data['message_count']}")
            
            # タイムスタンプは必ず存在する（上でチェック済み）
            # ローカルタイムゾーンに変換して表示
            time_format = '%Y/%m/%d %H:%M' if self.language == 'ja' else '%Y-%m-%d %H:%M'
            first = project_data["first_activity"].astimezone().strftime(time_format)
            last = project_data["last_activity"].astimezone().strftime(time_format)
            separator = ' 〜 ' if self.language == 'ja' else ' - '
            report.append(f"- {self.msg['period']}: {first}{separator}{last}")
                
            if project_data["topics"]:
                report.append(f"- {self.msg['main_topics']}:")
                for topic in project_data["topics"]:
                    report.append(f"  - {topic}")
                    
            if project_data["tool_usage"]:
                report.append(f"- {self.msg['tools_used']}:")
                for tool, count in project_data["tool_usage"].most_common(5):
                    report.append(f"  - {tool}: {count} {self.msg['times']}")
                    
            report.append("")
            
        # 全体のツール使用統計
        if analysis["tool_usage_overall"]:
            report.append(f"## {self.msg['tool_stats_overall']}")
            report.append("")
            for tool, count in analysis["tool_usage_overall"].most_common(10):
                report.append(f"- {tool}: {count} {self.msg['times']}")
            report.append("")
            
        # 日別アクティビティ
        if analysis["daily_activity"]:
            report.append(f"## {self.msg['daily_activity']}")
            report.append("")
            date_format = '%Y/%m/%d' if self.language == 'ja' else '%Y-%m-%d'
            for date, count in sorted(analysis["daily_activity"].items()):
                report.append(f"- {date.strftime(date_format)}: {count} {self.msg['items']}")
            report.append("")
            
        # 時間帯別アクティビティ
        if analysis["hourly_activity"] or True:  # 常に表示
            report.append(f"## {self.msg['hourly_activity']}")
            report.append("")
            
            # 最大値を取得（正規化のため）
            max_count = max(analysis["hourly_activity"].values()) if analysis["hourly_activity"] else 1
            
            # 24時間すべてを表示
            report.append("```")
            for hour in range(24):
                count = analysis["hourly_activity"].get(hour, 0)
                
                # 5段階で活動量を表現
                if count == 0:
                    level = 0
                else:
                    # より細かい段階分け
                    ratio = count / max_count
                    if ratio >= 0.8:
                        level = 5
                    elif ratio >= 0.6:
                        level = 4
                    elif ratio >= 0.4:
                        level = 3
                    elif ratio >= 0.2:
                        level = 2
                    else:
                        level = 1
                
                # ブロックで表現（GitHubスタイル）
                blocks = "■" * level + "□" * (5 - level)
                
                # 6時間ごとに区切り線
                if hour % 6 == 0 and hour > 0:
                    report.append("")
                    
                hour_label = f"{hour:02d}時" if self.language == 'ja' else f"{hour:02d}:00"
                report.append(f"{hour_label}: {blocks} {count:4d}")
            report.append("```")
            report.append("")
            
        return "\n".join(report)


def main():
    """メイン関数"""
    # 言語を事前に判定してヘルプメッセージを設定
    lang = get_language()
    
    if lang == 'ja':
        description = "Claude Codeとの会話履歴を分析しレポートを生成します"
        help_days = "過去何日分のデータを分析するか（デフォルト: 7日）"
        help_from = "開始日（YYYY-MM-DD形式）"
        help_to = "終了日（YYYY-MM-DD形式）"
        help_project = "特定のプロジェクトのみを対象にする"
        help_output = "レポートの出力先ファイル（指定しない場合は標準出力）"
        help_lang = "出力言語 (en/ja)"
    else:
        description = "Analyze Claude Code conversation history and generate reports"
        help_days = "Number of past days to analyze (default: 7)"
        help_from = "Start date (YYYY-MM-DD format)"
        help_to = "End date (YYYY-MM-DD format)"
        help_project = "Filter by specific project"
        help_output = "Output file path (stdout if not specified)"
        help_lang = "Output language (en/ja)"
    
    parser = argparse.ArgumentParser(description=description)
    
    # 期間指定オプション
    parser.add_argument(
        "--days", type=int, default=7,
        help=help_days
    )
    parser.add_argument(
        "--from", dest="from_date", type=str,
        help=help_from
    )
    parser.add_argument(
        "--to", dest="to_date", type=str,
        help=help_to
    )
    
    # その他のオプション
    parser.add_argument(
        "--project", type=str,
        help=help_project
    )
    parser.add_argument(
        "--output", "-o", type=str,
        help=help_output
    )
    parser.add_argument(
        "--lang", type=str, choices=['en', 'ja'],
        help=help_lang
    )
    
    args = parser.parse_args()
    
    # 期間の設定
    if args.from_date and args.to_date:
        from_date = datetime.strptime(args.from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        to_date = datetime.strptime(args.to_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
    else:
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=args.days)
        
    # 言語設定の決定
    language = get_language(args.lang)
    msg = MESSAGES[language]
    
    # レポート生成
    try:
        generator = ClaudeReportGenerator(language=language)
        
        print(msg['loading_data'].format(from_date.date(), to_date.date()), file=sys.stderr)
        generator.load_sessions(from_date, to_date, args.project)
        
        print(msg['analyzing_data'], file=sys.stderr)
        analysis = generator.analyze_sessions()
        
        print(msg['generating_report'], file=sys.stderr)
        report = generator.generate_markdown_report(analysis)
        
        # レポート出力
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(msg['report_saved'].format(args.output), file=sys.stderr)
        else:
            print(report)
            
    except Exception as e:
        print(f"{msg['error']}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()