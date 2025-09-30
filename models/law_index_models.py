# models/law_index_models.py
from dataclasses import dataclass
from typing import List

@dataclass
class LawItem:
    """法令項目データモデル"""
    id: str
    name: str
    category: str
    content: str
    last_updated: str

@dataclass
class LawSearchResult:
    """法令検索結果データモデル"""
    query: str
    results: List[LawItem]
    total_count: int
