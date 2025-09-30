# services/base_service.py
from abc import ABC, abstractmethod

class BaseService(ABC):
    """サービス基底クラス - 将来の拡張に対応"""
    
    def __init__(self):
        self.api_service = None
        self.storage_service = None
    
    @abstractmethod
    def load_data(self, identifier):
        """データ読み込み"""
        pass
    
    @abstractmethod
    def save_data(self, data):
        """データ保存"""
        pass
