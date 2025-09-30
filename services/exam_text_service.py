# services/exam_text_service.py
from .base_service import BaseService

class ExamTextService(BaseService):
    """問題文処理サービス"""
    
    def __init__(self):
        super().__init__()
        # 問題文関連の処理
    
    def load_pdf(self, file_path):
        """PDF問題文を読み込み"""
        pass
    
    def save_annotations(self, annotations):
        """注釈を保存"""
        pass
    
    def load_annotations(self, file_path):
        """注釈を読み込み"""
        pass
    
    def load_data(self, identifier):
        """データ読み込み"""
        pass
    
    def save_data(self, data):
        """データ保存"""
        pass
