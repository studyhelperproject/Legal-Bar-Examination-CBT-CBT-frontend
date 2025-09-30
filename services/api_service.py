# services/api_service.py
class APIService:
    """外部API連携サービス - 将来の拡張に対応"""
    
    def __init__(self):
        self.api_config = None
        self.is_connected = False
    
    def is_available(self):
        """API接続可能かチェック"""
        pass
    
    def fetch_pdf(self, file_path):
        """API経由でPDFを取得"""
        pass
    
    def save_annotations(self, annotations):
        """API経由で注釈を保存"""
        pass
    
    def fetch_law_data(self, law_id):
        """API経由で法令データを取得"""
        pass
    
    def save_answer(self, answer_data):
        """API経由で答案を保存"""
        pass
