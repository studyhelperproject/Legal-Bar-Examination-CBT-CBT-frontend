# services/base_service.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Optional

# Foward declaration for type hinting
class APIService: pass
class StorageService: pass

# データモデルを表すジェネリック型を定義
T = TypeVar('T')

class BaseService(Generic[T], ABC):
    """
    すべてのサービスクラスの基底となる抽象クラス（ABC）。

    データロードとセーブの共通インターフェースを定義します。
    具象サービスクラスは、特定のデータモデル（例: AnswerSheet, Memo）を
    扱うために、このクラスを継承し、抽象メソッドを実装する必要があります。

    Attributes:
        api_service (Optional['APIService']): API連携サービスへの参照。
        storage_service (Optional['StorageService']): ローカルストレージサービスへの参照。
    """

    def __init__(
        self,
        api_service: Optional['APIService'] = None,
        storage_service: Optional['StorageService'] = None
    ) -> None:
        """BaseServiceのコンストラクタ。

        Args:
            api_service (Optional[APIService]): APIサービスインスタンス。
            storage_service (Optional[StorageService]): ストレージサービスインスタンス。
        """
        self.api_service = api_service
        self.storage_service = storage_service

    @abstractmethod
    def load_data(self, identifier: Any) -> Optional[T]:
        """
        指定された識別子を使用してデータを読み込むための抽象メソッド。

        具象クラスは、ローカルストレージやAPIからデータを取得するロジックを実装します。

        Args:
            identifier (Any): データを一意に識別するためのキー（例: ID、ファイルパス）。

        Returns:
            Optional[T]: 読み込まれたデータモデルオブジェクト。見つからない場合はNone。
        """
        pass

    @abstractmethod
    def save_data(self, data: T) -> None:
        """
        データを永続化するための抽象メソッド。

        具象クラスは、ローカルストレージやAPIにデータを保存するロジックを実装します。

        Args:
            data (T): 保存するデータモデルオブジェクト。
        """
        pass
