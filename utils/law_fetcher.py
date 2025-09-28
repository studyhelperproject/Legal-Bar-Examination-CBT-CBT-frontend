# utils/law_fetcher.py
import requests
from PyQt6.QtCore import QThread, pyqtSignal

class LawFetcherThread(QThread):
    result_ready = pyqtSignal(tuple)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, law_id, parent=None):
        super().__init__(parent)
        self.law_id = law_id
        
    def run(self):
        try:
            r = requests.get(f"https://elaws.e-gov.go.jp/api/1/lawdata/{self.law_id}", timeout=15)
            r.raise_for_status()
            self.result_ready.emit((r.content.decode('utf-8-sig'),))
        except requests.RequestException as e:
            self.error_occurred.emit(f"エラー：法令データを取得できませんでした。\n{e}")
        except Exception as e:
            self.error_occurred.emit(f"予期せぬエラーが発生しました: {e}")