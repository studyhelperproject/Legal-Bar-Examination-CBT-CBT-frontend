"""
アプリケーションのエントリーポイント。

このスクリプトは、PyQt6アプリケーションを初期化し、メインウィンドウである
MainWindowを生成・表示して、アプリケーションのイベントループを開始します。
また、プロジェクトのルートディレクトリをPythonのパスに追加し、
他のモジュール（ui, utilsなど）を正しくインポートできるように設定します。
"""
import sys
import os
from PyQt6.QtWidgets import QApplication

# このファイル(main.py)があるディレクトリの絶対パスを取得し、
# Pythonがモジュールを探しに行く場所のリスト（sys.path）に追加します。
# これにより、uiフォルダやutilsフォルダなどのプロジェクト内モジュールを
# 正しく見つけられるようになります。
current_dir: str = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# メインウィンドウクラスをインポートします
from ui.main_window import MainWindow

if __name__ == "__main__":
    # 1. PyQtアプリケーションインスタンスを作成します。
    # sys.argvにより、コマンドライン引数をアプリケーションに渡すことができます。
    app: QApplication = QApplication(sys.argv)

    # 2. メインウィンドウのインスタンスを作成します。
    window: MainWindow = MainWindow()

    # 3. ウィンドウを表示します。
    window.show()

    # 4. アプリケーションのイベントループを開始します。
    # ウィンドウが閉じられるなどの終了イベントが発生するまで、プログラムはこの行で待機します。
    # app.exec()が返す終了コードでプロセスを終了します。
    sys.exit(app.exec())
