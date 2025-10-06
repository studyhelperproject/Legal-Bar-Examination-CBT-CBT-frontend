# models/answer_models.py
from dataclasses import dataclass
from typing import List

@dataclass
class AnswerSheet:
    """答案用紙全体を表現するデータモデル。

    Attributes:
        question_number (int): 問題番号。
        pages (List['AnswerPage']): 答案の各ページを格納するリスト。
        total_characters (int): 答案全体の総文字数。
        total_lines (int): 答案全体の総行数。
    """
    question_number: int
    pages: List['AnswerPage']
    total_characters: int
    total_lines: int

@dataclass
class AnswerPage:
    """答案の単一ページを表現するデータモデル。

    Attributes:
        page_number (int): ページ番号。
        content (str): ページの内容（テキスト）。
        character_count (int): このページの文字数。
        line_count (int): このページの行数。
    """
    page_number: int
    content: str
    character_count: int
    line_count: int
