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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter


class ClaudeReportGenerator:
    """Claude Codeの会話履歴を分析しレポートを生成するクラス"""
    
    def __init__(self, base_path: str = "/Users/zabaglione/.claude/projects"):
        self.base_path = Path(base_path)
        self.sessions = []
        
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
            return f"画像ファイル: {filename}"
            
        # Base64データの検出
        if 'data:image' in content or (len(content) > 1000 and re.match(r'^[A-Za-z0-9+/\s]+={0,2}$', content)):
            return "画像データの処理"
            
        # スクリーンショットパスの検出
        if 'screenshot' in content.lower() or 'screencapture' in content.lower():
            return "スクリーンショットの解析"
            
        # ファイルパスの検出（Read/Write系の操作）
        file_path_match = re.search(r'(?:^|\s)(/[\w\-./]+\.\w+)', content)
        if file_path_match:
            filepath = file_path_match.group(1)
            filename = os.path.basename(filepath)
            
            # ファイル操作の種類を判定
            if '作成' in content or 'create' in content.lower() or '生成' in content:
                return f"ファイル作成: {filename}"
            elif '編集' in content or 'edit' in content.lower() or '修正' in content:
                return f"ファイル編集: {filename}"
            elif '読み' in content or 'read' in content.lower() or '確認' in content:
                return f"ファイル確認: {filename}"
            else:
                return f"ファイル操作: {filename}"
                
        # URLの検出
        url_match = re.search(r'https?://[^\s]+', content)
        if url_match:
            url = url_match.group(0)
            domain = re.search(r'https?://([^/]+)', url)
            if domain:
                return f"Web参照: {domain.group(1)}"
                
        # コード記述依頼の検出
        code_keywords = ['実装', 'コード', 'プログラム', '関数', 'クラス', 'メソッド', 
                        'implement', 'code', 'function', 'class', 'method']
        for keyword in code_keywords:
            if keyword in content.lower():
                # より具体的な内容を抽出
                if '作成' in content or '作って' in content or 'create' in content.lower():
                    return "コード実装依頼"
                elif 'エラー' in content or 'error' in content.lower() or '修正' in content:
                    return "エラー修正・デバッグ"
                else:
                    return "コード関連の作業"
                    
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
                    return f"[{tool_name}] {cmd_name}コマンド実行"
                    
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
                    timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    
                    # 最初と最後のアクティビティを記録
                    if project_data["first_activity"] is None or timestamp < project_data["first_activity"]:
                        project_data["first_activity"] = timestamp
                    if project_data["last_activity"] is None or timestamp > project_data["last_activity"]:
                        project_data["last_activity"] = timestamp
                        
                    # 日別・時間別アクティビティ
                    analysis["daily_activity"][timestamp.date()] += 1
                    analysis["hourly_activity"][timestamp.hour] += 1
                
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
        report.append("# Claude Code 会話履歴レポート")
        report.append(f"\n生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        
        # アクティブなプロジェクト数をカウント
        active_projects = sum(1 for p in analysis["projects"].values() 
                            if p["sessions"] and p["first_activity"] and p["last_activity"])
        
        report.append(f"総セッション数: {analysis['total_sessions']}")
        report.append(f"アクティブプロジェクト数: {active_projects}")
        report.append("")
        
        # プロジェクト別サマリー
        report.append("## プロジェクト別サマリー")
        report.append("")
        
        for project_name, project_data in sorted(analysis["projects"].items()):
            if not project_data["sessions"]:
                continue
            
            # タイムスタンプがないプロジェクトはスキップ
            if not project_data["first_activity"] or not project_data["last_activity"]:
                continue
                
            report.append(f"### 📁 {project_name}")
            report.append(f"- セッション数: {len(project_data['sessions'])}")
            report.append(f"- メッセージ数: {project_data['message_count']}")
            
            # タイムスタンプは必ず存在する（上でチェック済み）
            first = project_data["first_activity"].strftime('%Y/%m/%d %H:%M')
            last = project_data["last_activity"].strftime('%Y/%m/%d %H:%M')
            report.append(f"- 期間: {first} 〜 {last}")
                
            if project_data["topics"]:
                report.append("- 主な話題:")
                for topic in project_data["topics"]:
                    report.append(f"  - {topic}")
                    
            if project_data["tool_usage"]:
                report.append("- 使用ツール:")
                for tool, count in project_data["tool_usage"].most_common(5):
                    report.append(f"  - {tool}: {count}回")
                    
            report.append("")
            
        # 全体のツール使用統計
        if analysis["tool_usage_overall"]:
            report.append("## ツール使用統計（全体）")
            report.append("")
            for tool, count in analysis["tool_usage_overall"].most_common(10):
                report.append(f"- {tool}: {count}回")
            report.append("")
            
        # 日別アクティビティ
        if analysis["daily_activity"]:
            report.append("## 日別アクティビティ")
            report.append("")
            for date, count in sorted(analysis["daily_activity"].items()):
                report.append(f"- {date.strftime('%Y/%m/%d')}: {count}件")
            report.append("")
            
        # 時間帯別アクティビティ
        if analysis["hourly_activity"]:
            report.append("## 時間帯別アクティビティ")
            report.append("")
            for hour in sorted(analysis["hourly_activity"].keys()):
                count = analysis["hourly_activity"][hour]
                bar = "█" * (count // 5) if count > 0 else ""
                report.append(f"- {hour:02d}時: {bar} ({count}件)")
            report.append("")
            
        return "\n".join(report)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Claude Codeとの会話履歴を分析しレポートを生成します"
    )
    
    # 期間指定オプション
    parser.add_argument(
        "--days", type=int, default=7,
        help="過去何日分のデータを分析するか（デフォルト: 7日）"
    )
    parser.add_argument(
        "--from", dest="from_date", type=str,
        help="開始日（YYYY-MM-DD形式）"
    )
    parser.add_argument(
        "--to", dest="to_date", type=str,
        help="終了日（YYYY-MM-DD形式）"
    )
    
    # その他のオプション
    parser.add_argument(
        "--project", type=str,
        help="特定のプロジェクトのみを対象にする"
    )
    parser.add_argument(
        "--output", "-o", type=str,
        help="レポートの出力先ファイル（指定しない場合は標準出力）"
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
        
    # レポート生成
    try:
        generator = ClaudeReportGenerator()
        
        print(f"データを読み込み中... (期間: {from_date.date()} 〜 {to_date.date()})", file=sys.stderr)
        generator.load_sessions(from_date, to_date, args.project)
        
        print("データを分析中...", file=sys.stderr)
        analysis = generator.analyze_sessions()
        
        print("レポートを生成中...", file=sys.stderr)
        report = generator.generate_markdown_report(analysis)
        
        # レポート出力
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"レポートを {args.output} に保存しました", file=sys.stderr)
        else:
            print(report)
            
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()