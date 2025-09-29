#!/bin/bash
# 司法試験CBTシミュレーター起動スクリプト

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境をアクティベート
source venv/bin/activate

# アプリケーションを起動
python main.py
