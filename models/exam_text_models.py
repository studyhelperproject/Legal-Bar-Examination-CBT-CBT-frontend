# models/exam_text_models.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PDFDocument:
    """PDF文書データモデル"""
    file_path: str
    total_pages: int
    current_page: int
    annotations: List['Annotation']
    metadata: Optional[dict] = None

@dataclass
class Annotation:
    """注釈データモデル"""
    id: str
    type: str  # 'pen', 'marker', 'text', 'shape'
    page: int
    data: dict
    created_at: str
    modified_at: str
