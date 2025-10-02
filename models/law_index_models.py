# models/law_index_models.py
from dataclasses import dataclass
from typing import List

@dataclass
class LawItem:
    """単一の法令項目を表現するデータモデル。

    Attributes:
        id (str): 法令の一意なID。
        name (str): 法令の名称（例: 「民法」）。
        category (str): 法令のカテゴリ（例: 「憲法」「民事法」）。
        content (str): 法令の本文。
        last_updated (str): 最終更新日（ISO 8601形式）。
    """
    id: str
    name: str
    category: str
    content: str
    last_updated: str

@dataclass
class LawSearchResult:
    """法令検索の実行結果を表現するデータモデル。

    Attributes:
        query (str): 実行された検索クエリ。
        results (List[LawItem]): 検索結果に合致した法令項目のリスト。
        total_count (int): 検索結果の総数。
    """
    query: str
    results: List[LawItem]
    total_count: int
