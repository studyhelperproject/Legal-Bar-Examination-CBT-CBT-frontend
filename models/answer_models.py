# models/answer_models.py
from dataclasses import dataclass
from typing import List

@dataclass
class AnswerSheet:
    """答案用紙データモデル"""
    question_number: int
    pages: List['AnswerPage']
    total_characters: int
    total_lines: int

@dataclass
class AnswerPage:
    """答案ページデータモデル"""
    page_number: int
    content: str
    character_count: int
    line_count: int
