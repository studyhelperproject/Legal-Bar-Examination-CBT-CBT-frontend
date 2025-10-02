# services/law_index_service.py
from .base_service import BaseService
from models.law_index_models import LawItem, LawSearchResult
from utils.constants import LAW_DATA
from typing import List, Optional, Dict, Any

class LawIndexService(BaseService[List[LawItem]]):
    """法令データの管理と操作を行うサービスクラス。

    法令一覧の読み込み、キーワード検索、および個別の法令内容の取得機能を提供します。
    """

    def __init__(self) -> None:
        """LawIndexServiceのコンストラクタ。

        初期化時に、`utils.constants.LAW_DATA` から法令マスターデータをロードします。
        """
        super().__init__()
        self.law_master_data: List[LawItem] = self.load_data("constants")

    def load_law_list(self) -> Dict[str, Any]:
        """カテゴリ別にグループ化された法令一覧を取得する。

        Returns:
            Dict[str, Any]: `utils.constants.LAW_DATA` と同じ構造の法令データ。
        """
        return LAW_DATA

    def load_law_content(self, law_id: str) -> Optional[LawItem]:
        """指定された法令IDに対応する法令データを取得する。

        実際には `LawFetcherThread` などを介してe-Gov APIから内容を取得するが、
        ここではマスターデータから該当項目を返すダミー実装とします。

        Args:
            law_id (str): 取得する法令のID。

        Returns:
            Optional[LawItem]: 見つかった法令データ。存在しない場合はNone。
        """
        for item in self.law_master_data:
            if item.id == law_id:
                # 本来はここでAPIから取得した本文(content)をセットする
                print(f"法令 (ID: {law_id}) の内容取得を試みました。")
                return item
        return None

    def search_laws(self, keyword: str) -> LawSearchResult:
        """指定されたキーワードで法令を検索する。

        Args:
            keyword (str): 検索キーワード。

        Returns:
            LawSearchResult: 検索結果。
        """
        if not keyword:
            return LawSearchResult(query=keyword, results=[], total_count=0)

        results = [
            item for item in self.law_master_data
            if keyword.lower() in item.name.lower()
        ]
        return LawSearchResult(query=keyword, results=results, total_count=len(results))

    def load_data(self, identifier: str) -> List[LawItem]:
        """BaseServiceから継承したメソッド。法令マスターデータを読み込む。

        Args:
            identifier (str): データソースの識別子（現在は "constants" のみサポート）。

        Returns:
            List[LawItem]: 読み込まれた全法令のリスト。
        """
        if identifier == "constants":
            master_list = []
            for category, laws in LAW_DATA.items():
                for name, law_id in laws.items():
                    master_list.append(LawItem(
                        id=law_id,
                        name=name,
                        category=category,
                        content="",  # 本文は遅延ロード
                        last_updated="" # 更新日も遅延ロード
                    ))
            return master_list
        return []

    def save_data(self, data: List[LawItem]) -> None:
        """BaseServiceから継承したメソッド。法令データは読み取り専用のため、何もしない。

        Args:
            data (List[LawItem]): 保存するデータ（未使用）。
        """
        # 法令データは静的なマスターデータなので、保存処理は不要
        print("LawIndexService.save_dataは呼び出されましたが、処理は行われません。")
        pass
