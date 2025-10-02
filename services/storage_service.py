# services/storage_service.py
import json
import os
from typing import Dict, Any, Optional, Union, List
from models.session_models import SessionData

class StorageService:
    """ローカルファイルシステムへのデータ永続化を管理するサービスクラス。

    JSON形式のデータやセッション情報の保存・読み込み機能を提供します。
    """

    def __init__(self, base_path: str = "data") -> None:
        """StorageServiceのコンストラクタ。

        Args:
            base_path (str): データを保存する基準ディレクトリのパス。
                             存在しない場合は自動的に作成されます。
        """
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def get_path(self, file_name: str) -> str:
        """ベースパスとファイル名を結合して完全なファイルパスを取得する。

        Args:
            file_name (str): ファイル名。

        Returns:
            str: 完全なファイルパス。
        """
        return os.path.join(self.base_path, file_name)

    def save_json(self, file_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """データをJSONファイルとしてローカルに保存する。

        Args:
            file_name (str): 保存するファイル名。
            data (Union[Dict, List]): 保存するデータ（辞書または辞書のリスト）。
        """
        file_path = self.get_path(file_name)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"データを {file_path} に保存しました。")
        except IOError as e:
            print(f"ファイル保存中にエラーが発生しました: {file_path}, {e}")

    def load_json(self, file_name: str) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """ローカルのJSONファイルからデータを読み込む。

        Args:
            file_name (str): 読み込むファイル名。

        Returns:
            Optional[Union[Dict, List]]: 読み込まれたデータ。ファイルが存在しない場合はNone。
        """
        file_path = self.get_path(file_name)
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"ファイル読み込み中にエラーが発生しました: {file_path}, {e}")
            return None

    def save_session(self, session_data: SessionData) -> None:
        """試験セッションデータを保存する。

        セッションIDをファイル名として使用します。

        Args:
            session_data (SessionData): 保存するセッションデータ。
        """
        # SessionDataオブジェクトを辞書に変換する必要がある
        session_dict = session_data.__dict__
        # ネストされたオブジェクトも辞書に変換
        # この部分はSessionDataの構造に依存するため、より複雑な変換が必要な場合がある
        for key, value in session_dict.items():
            if hasattr(value, '__dict__'):
                session_dict[key] = value.__dict__

        file_name = f"session_{session_data.session_id}.json"
        self.save_json(file_name, session_dict)

    def load_session(self, session_id: str) -> Optional[SessionData]:
        """試験セッションデータを読み込む。

        Args:
            session_id (str): 読み込むセッションのID。

        Returns:
            Optional[SessionData]: 読み込まれたセッションデータ。見つからない場合はNone。
        """
        file_name = f"session_{session_id}.json"
        data = self.load_json(file_name)
        if data and isinstance(data, dict):
            # 辞書からSessionDataオブジェクトへ再構築
            # ここも複雑なオブジェクトのデシリアライズが必要な場合がある
            try:
                return SessionData(**data)
            except TypeError as e:
                print(f"セッションデータのデシリアライズに失敗しました: {e}")
                return None
        return None
