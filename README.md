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
.
├── assets/
│   └── answer_template.pdf         # 答案テンプレートPDF
├── config/                         # 設定層
│   ├── __init__.py
│   ├── api_config.py               # API設定
│   ├── settings.py                 # アプリケーション設定
│   └── ui_config.py                # UI設定
├── models/                         # データモデル層
│   ├── __init__.py
│   ├── answer_models.py            # 答案関連データモデル
│   ├── exam_text_models.py         # 問題文関連データモデル
│   ├── law_index_models.py         # 法令関連データモデル
│   ├── memo_models.py              # メモ関連データモデル
│   └── session_models.py           # セッション関連データモデル
├── services/                       # サービス層（ビジネスロジック）
│   ├── __init__.py
│   ├── answer_service.py           # 答案処理サービス
│   ├── api_service.py              # 外部API連携サービス
│   ├── base_service.py             # サービス基底クラス
│   ├── exam_text_service.py        # 問題文処理サービス
│   ├── law_index_service.py        # 法令処理サービス
│   ├── memo_service.py             # メモ処理サービス
│   └── storage_service.py          # データ保存サービス
├── tests/                          # テスト層
│   └── test_main.py                # メインテストスクリプト
├── ui/                             # UI層
│   ├── __init__.py
│   ├── components.py               # 共通UIコンポーネント
│   ├── main_window.py              # メインウィンドウ
│   ├── dialogs/                    # ダイアログ
│   ├── handlers/                   # イベントハンドラ
│   ├── screens/                    # 各画面
│   └── widgets/                    # カスタムUIウィジェット
└── utils/                          # ユーティリティ層
    ├── __init__.py
    ├── answer_utils.py             # 答案処理ユーティリティ
    ├── api_utils.py                # API連携ユーティリティ
    ├── constants.py                # 定数定義
    ├── law_fetcher.py              # 法令データ取得
    ├── law_utils.py                # 法文処理ユーティリティ
    ├── pdf_utils.py                # PDF処理ユーティリティ
    └── xml_parser.py               # XMLパーサー
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
