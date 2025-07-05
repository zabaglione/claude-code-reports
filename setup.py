from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claude-code-report",
    version="1.0.0",
    author="z_zabaglione",
    author_email="",
    description="Claude Codeとの会話履歴を分析しレポートを生成するCLIツール",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zabaglione/claude-code-reports",
    py_modules=["claude_report"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "claude-report=claude_report:main",
        ],
    },
)