import sys
import os
from PyQt6.QtWidgets import QApplication

# このファイル(main.py)があるディレクトリの絶対パスを取得し、
# Pythonがモジュールを探しに行く場所のリストに追加します。
# これにより、uiフォルダやutilsフォルダを正しく見つけられるようになります。
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# モジュール化したMainWindowをインポートします
from ui.main_window import MainWindow

if __name__ == "__main__":
    # アプリケーションを開始します
    app = QApplication(sys.argv)
    # MainWindowのインスタンスを作成します
    window = MainWindow()
    # ウィンドウを表示します
    window.show()
    # アプリケーションのイベントループを開始し、ウィンドウが閉じられるまで待機します
    sys.exit(app.exec())
