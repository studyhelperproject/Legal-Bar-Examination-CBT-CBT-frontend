# models/memo_models.py
from dataclasses import dataclass

@dataclass
class Memo:
    """メモデータモデル"""
    id: str
    title: str
    content: str
    created_at: str
    modified_at: str
