# models/session_models.py
from dataclasses import dataclass
from typing import Dict, List
from models.answer_models import AnswerSheet
from models.exam_text_models import PDFDocument
from models.law_index_models import LawItem
from models.memo_models import Memo

@dataclass
class SessionData:
    """試験中のユーザーセッション全体の状態を表現するデータモデル。

    Attributes:
        session_id (str): セッションの一意なID。
        remaining_time (int): 試験の残り時間（秒単位）。
        exam_text_data (PDFDocument): 現在の試験問題（PDF）の状態。
        law_index_data (List[LawItem]): 法令集のデータ。
        answer_data (Dict[int, AnswerSheet]): 答案データ（問題番号をキーとする辞書）。
        memo_data (List[Memo]): 作成された全メモのリスト。
        created_at (str): セッションの開始日時（ISO 8601形式）。
        modified_at (str): セッションの最終更新日時（ISO 8601形式）。
    """
    session_id: str
    remaining_time: int
    exam_text_data: PDFDocument
    law_index_data: List[LawItem]
    answer_data: Dict[int, AnswerSheet]
    memo_data: List[Memo]
    created_at: str
    modified_at: str
