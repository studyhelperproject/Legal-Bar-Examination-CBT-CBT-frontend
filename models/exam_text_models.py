# models/exam_text_models.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class PDFDocument:
    """PDF文書全体を表現するデータモデル。

    Attributes:
        file_path (str): PDFファイルのパス。
        total_pages (int): PDFの総ページ数。
        current_page (int): 現在表示しているページ番号。
        annotations (List['Annotation']): 文書内の全注釈のリスト。
        metadata (Optional[Dict[str, Any]]): PDFのメタデータ（作者、タイトルなど）。
    """
    file_path: str
    total_pages: int
    current_page: int
    annotations: List['Annotation']
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Annotation:
    """文書内の単一の注釈を表現するデータモデル。

    Attributes:
        id (str): 注釈の一意なID。
        type (str): 注釈の種類（例: 'pen', 'marker', 'text', 'shape'）。
        page (int): 注釈が追加されたページ番号。
        data (Dict[str, Any]): 注釈固有のデータ（座標、色、テキスト内容など）。
        created_at (str): 注釈の作成日時（ISO 8601形式）。
        modified_at (str): 注釈の最終更新日時（ISO 8601形式）。
    """
    id: str
    type: str  # 'pen', 'marker', 'text', 'shape'
    page: int
    data: Dict[str, Any]
    created_at: str
    modified_at: str
