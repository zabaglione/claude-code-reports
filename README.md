# Claude Code Report Generator

[日本語版 README](README.ja.md)

A CLI tool to analyze Claude Code conversation history and generate project-based and period-based summary reports.

## Overview

This tool parses Claude Code conversation history (JSONL files) and generates Markdown reports containing:

- Project-wise activity summaries
- Tool usage statistics
- Daily and hourly activity analysis
- Smart content summarization (including images and file operations)

## Features

- 📊 **Detailed Statistics**: Aggregates session counts, message counts, and time ranges per project
- 🔧 **Tool Usage Analysis**: Tracks frequency of Read, Write, Edit, Bash, WebFetch and other tools
- 📅 **Flexible Date Filtering**: Filter by number of days or specific date ranges
- 🎯 **Smart Summarization**: Auto-categorizes images, code requests, error fixes, etc.
- 🚀 **Fast Processing**: Uses only Python standard library, no external dependencies

## Installation

```bash
# Clone the repository
git clone https://github.com/zabaglione/claude-code-reports.git
cd claude-code-reports

# Make executable
chmod +x claude_report.py
```

## Usage

### Basic Usage

```bash
# Generate report for the last 7 days (default)
python3 claude_report.py

# Generate report for the last 30 days
python3 claude_report.py --days 30

# Specify date range
python3 claude_report.py --from 2025-07-01 --to 2025-07-05

# Filter by project
python3 claude_report.py --project myproject

# Save to file
python3 claude_report.py -o report.md
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--days` | Number of past days to analyze | 7 |
| `--from` | Start date (YYYY-MM-DD format) | - |
| `--to` | End date (YYYY-MM-DD format) | - |
| `--project` | Filter by project name | - |
| `--output`, `-o` | Output file path | stdout |

## Report Contents

The generated report includes:

### Project Summaries
- Session and message counts
- Activity period (first and last activity)
- Main topics (auto-summarized)
  - Image file processing
  - Code implementation requests
  - Error fixes and debugging
  - File operations (create/edit/read)
  - Web references
- Tool usage counts (top 5)

### Overall Statistics
- Tool usage statistics across all projects
- Daily activity breakdown
- Hourly activity visualization (GitHub-style blocks)

## Requirements

- Python 3.6 or higher
- Claude Code conversation history directory (`~/.claude/projects/`)

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Author

z_zabaglione ([@z_zabaglione](https://x.com/z_zabaglione))