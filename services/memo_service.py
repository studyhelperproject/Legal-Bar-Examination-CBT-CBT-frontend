# services/memo_service.py
import uuid
import datetime
from .base_service import BaseService
from models.memo_models import Memo
from typing import List, Optional, Any

class MemoService(BaseService[List[Memo]]):
    """メモデータのCRUD操作を管理するサービスクラス。

    メモの作成、保存、一覧読み込み、削除機能を提供します。
    データはStorageServiceを介して永続化されます。
    """
    
    MEMO_FILE_IDENTIFIER = "memos.json"

    def __init__(self, storage_service: Optional['StorageService'] = None) -> None:
        """MemoServiceのコンストラクタ。

        Args:
            storage_service (Optional[StorageService]): データ永続化のためのストレージサービス。
        """
        super().__init__(storage_service=storage_service)
        self.memos: List[Memo] = self.load_data(self.MEMO_FILE_IDENTIFIER) or []

    def save_memo(self, memo_data: Memo) -> Memo:
        """メモを保存または更新する。

        IDが存在しない場合は新しいメモとして追加し、IDが存在する場合は既存のメモを更新する。
        更新時にはタイムスタンプも更新される。

        Args:
            memo_data (Memo): 保存または更新するメモデータ。

        Returns:
            Memo: 保存または更新されたメモデータ（新しいIDやタイムスタンプが設定されている）。
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        existing_memo_index = -1
        if memo_data.id:
            for i, m in enumerate(self.memos):
                if m.id == memo_data.id:
                    existing_memo_index = i
                    break

        if existing_memo_index != -1:
            # 更新
            memo_data.modified_at = now
            self.memos[existing_memo_index] = memo_data
        else:
            # 新規作成
            memo_data.id = str(uuid.uuid4())
            memo_data.created_at = now
            memo_data.modified_at = now
            self.memos.append(memo_data)

        self.save_data(self.memos)
        return memo_data

    def load_memos(self) -> List[Memo]:
        """保存されているすべてのメモをリストとして取得する。

        Returns:
            List[Memo]: メモデータのリスト。
        """
        return self.memos

    def delete_memo(self, memo_id: str) -> bool:
        """指定されたIDのメモを削除する。

        Args:
            memo_id (str): 削除するメモのID。

        Returns:
            bool: 削除に成功した場合はTrue、該当IDのメモが見つからなかった場合はFalse。
        """
        initial_len = len(self.memos)
        self.memos = [m for m in self.memos if m.id != memo_id]
        if len(self.memos) < initial_len:
            self.save_data(self.memos)
            return True
        return False

    def load_data(self, identifier: str) -> Optional[List[Memo]]:
        """BaseServiceから継承したメソッド。ストレージからメモデータを読み込む。

        Args:
            identifier (str): 読み込むファイル名（識別子）。

        Returns:
            Optional[List[Memo]]: 読み込まれたメモのリスト。データがない場合はNone。
        """
        if self.storage_service:
            data = self.storage_service.load_json(identifier)
            if data:
                return [Memo(**item) for item in data]
        return None

    def save_data(self, data: List[Memo]) -> None:
        """BaseServiceから継承したメソッド。メモデータをストレージに保存する。

        Args:
            data (List[Memo]): 保存するメモのリスト。
        """
        if self.storage_service:
            memo_dicts = [memo.__dict__ for memo in data]
            self.storage_service.save_json(self.MEMO_FILE_IDENTIFIER, memo_dicts)
