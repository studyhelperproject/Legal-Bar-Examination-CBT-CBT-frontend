# 司法試験CBTシミュレーター

司法試験のCBT（Computer Based Testing）システムをシミュレートするPythonアプリケーションです。

## 機能

- **PDF問題文表示**: PDF形式の問題文を表示・注釈可能
- **法令データベース**: 各種法令の検索・表示機能
- **答案作成**: Word/PDF形式での答案出力
- **タイマー機能**: 試験時間の管理
- **メモ機能**: 試験中のメモ取り
- **日本語入力対応**: ローマ字・かな入力の切り替え


## ファイル構成
機能単位で分割しています

```
cbt_simulator/
├── ui/
│   ├── screens/                    # 画面層（UI表示）
│   │   ├── __init__.py
│   │   ├── exam_text_screen.py     # 司法試験問題画面
│   │   ├── law_index_screen.py     # 法律索引画面
│   │   ├── answer_screen.py        # 答案入力画面
│   │   └── memo_screen.py          # メモ画面
│   ├── main_window.py              # メインウィンドウ（統合）
│   └── dialogs/                    # ダイアログ層
│       ├── __init__.py
│       ├── timer_dialog.py         # タイマー設定ダイアログ
│       └── bookmark_dialog.py      # 付箋管理ダイアログ
├── services/                       # サービス層（ビジネスロジック・API連携）
│   ├── __init__.py
│   ├── exam_text_service.py        # 問題文処理サービス
│   ├── law_index_service.py        # 法令処理サービス
│   ├── answer_service.py           # 答案処理サービス
│   ├── memo_service.py             # メモ処理サービス
│   ├── api_service.py              # 外部API連携サービス
│   ├── storage_service.py          # データ保存サービス
│   └── base_service.py             # サービス基底クラス
├── models/                         # データモデル層
│   ├── __init__.py
│   ├── exam_text_models.py         # 問題文関連データモデル
│   ├── law_index_models.py         # 法令関連データモデル
│   ├── answer_models.py            # 答案関連データモデル
│   ├── memo_models.py              # メモ関連データモデル
│   └── session_models.py           # セッション関連データモデル
├── config/                         # 設定層
│   ├── __init__.py
│   ├── settings.py                 # アプリケーション設定
│   ├── api_config.py               # API設定
│   └── ui_config.py                # UI設定
└── utils/                          # ユーティリティ層
    ├── __init__.py
    ├── pdf_utils.py                # PDF処理ユーティリティ
    ├── law_utils.py                # 法文処理ユーティリティ
    ├── answer_utils.py             # 答案処理ユーティリティ
    └── api_utils.py                # API連携ユーティリティ
```

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


## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
