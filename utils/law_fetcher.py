# utils/law_fetcher.py
"""e-Gov法令APIから法令データを非同期で取得するためのスレッド機能を提供します。"""

import requests
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from typing import Optional

class LawFetcherThread(QThread):
    """e-Gov法令APIから指定された法令データを取得するためのワーカースレッド。

    UIのフリーズを防ぐため、ネットワークリクエストをバックグラウンドで実行します。

    Signals:
        result_ready (pyqtSignal):
            法令データの取得に成功した際に、法令のテキストデータ（XML形式）を含むタプルを送信します。
        error_occurred (pyqtSignal):
            データ取得中にエラーが発生した際に、エラーメッセージ（str）を送信します。
    """
    result_ready = pyqtSignal(tuple)
    error_occurred = pyqtSignal(str)

    def __init__(self, law_id: str, parent: Optional[QObject] = None) -> None:
        """LawFetcherThreadのコンストラクタ。

        Args:
            law_id (str): 取得対象の法令ID（例: "昭和二十二年法律第六十七号"）。
            parent (Optional[QObject]): 親オブジェクト。デフォルトはNone。
        """
        super().__init__(parent)
        self.law_id = law_id

    def run(self) -> None:
        """スレッドのメイン処理。e-Gov法令APIにリクエストを送信し、結果をシグナルで通知する。"""
        try:
            url = f"https://elaws.e-gov.go.jp/api/1/lawdata/{self.law_id}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            # utf-8-sigでBOMを処理
            content = response.content.decode('utf-8-sig')
            self.result_ready.emit((content,))
        except requests.RequestException as e:
            self.error_occurred.emit(f"エラー：法令データを取得できませんでした。\n{e}")
        except Exception as e:
            self.error_occurred.emit(f"予期せぬエラーが発生しました: {e}")