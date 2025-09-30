# models/session_models.py
from dataclasses import dataclass

@dataclass
class SessionData:
    """セッションデータモデル"""
    session_id: str
    remaining_time: int
    exam_text_data: dict
    law_index_data: dict
    answer_data: dict
    memo_data: dict
    created_at: str
    modified_at: str
