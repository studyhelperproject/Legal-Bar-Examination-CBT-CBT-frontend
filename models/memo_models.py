# models/memo_models.py
from dataclasses import dataclass

@dataclass
class Memo:
    """ユーザーが作成する単一のメモを表現するデータモデル。

    Attributes:
        id (str): メモの一意なID。
        title (str): メモのタイトル。
        content (str): メモの本文。
        created_at (str): メモの作成日時（ISO 8601形式）。
        modified_at (str): メモの最終更新日時（ISO 8601形式）。
    """
    id: str
    title: str
    content: str
    created_at: str
    modified_at: str
