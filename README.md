# 司法試験CBTシミュレーター

司法試験のCBT（Computer Based Testing）システムをシミュレートするPythonアプリケーションです。

## 機能

- **PDF問題文表示**: PDF形式の問題文を表示・注釈可能
- **法令データベース**: 各種法令の検索・表示機能
- **答案作成**: Word/PDF形式での答案出力
- **タイマー機能**: 試験時間の管理
- **メモ機能**: 試験中のメモ取り
- **日本語入力対応**: ローマ字・かな入力の切り替え

## 必要な環境

- Python 3.8以上
- macOS, Windows, Linux対応

## インストール

1. リポジトリをクローン
```bash
git clone https://github.com/Legal-Bar-Examination-CBT/Legal-Bar-Examination-CBT-CBT-frontend.git
cd Legal-Bar-Examination-CBT-CBT-frontend
```

2. 仮想環境を作成・アクティベート
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

## 起動方法

### 方法1: 起動スクリプトを使用

**macOS/Linux:**
```bash
./run.sh
```

**Windows:**
```cmd
run.bat
```

### 方法2: 直接実行

```bash
# 仮想環境をアクティベート後
python main.py
```

## 使用方法

1. アプリケーションを起動
2. 「問題PDFを開く」ボタンで問題文を読み込み
3. 左側のツールバーで注釈ツールを選択
4. 法令データベースで関連法令を検索
5. 答案タブで答案を作成
6. 「Word保存」または「書き込みを保存」で結果を保存

## ファイル構成

```
CBT_Simulator/
├── main.py              # メインアプリケーション
├── ui/                  # UIコンポーネント
│   ├── main_window.py   # メインウィンドウ
│   └── widgets.py       # カスタムウィジェット
├── utils/               # ユーティリティ
│   ├── constants.py     # 定数定義
│   ├── law_fetcher.py   # 法令データ取得
│   └── xml_parser.py    # XML解析
├── assets/              # アセットファイル
│   └── answer_template.pdf
├── requirements.txt     # 依存関係
├── run.sh              # 起動スクリプト(macOS/Linux)
├── run.bat             # 起動スクリプト(Windows)
└── README.md           # このファイル
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。