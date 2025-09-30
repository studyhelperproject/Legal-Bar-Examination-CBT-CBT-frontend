# services/memo_service.py
from .base_service import BaseService

class MemoService(BaseService):
    """メモ処理サービス"""
    
    def __init__(self):
        super().__init__()
        # メモ関連の処理
    
    def save_memo(self, memo_data):
        """メモを保存"""
        pass
    
    def load_memos(self):
        """メモ一覧を読み込み"""
        pass
    
    def delete_memo(self, memo_id):
        """メモを削除"""
        pass
    
    def load_data(self, identifier):
        """データ読み込み"""
        pass
    
    def save_data(self, data):
        """データ保存"""
        pass
