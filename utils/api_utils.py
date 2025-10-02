# utils/api_utils.py
import requests
from typing import Dict, Any, Optional

class APIUtils:
    """API連携に関する共通処理を提供するユーティリティクラス。"""

    @staticmethod
    def make_api_request(
        url: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """指定されたURLにAPIリクエストを送信し、JSONレスポンスを返す。

        Args:
            url (str): リクエストを送信するAPIエンドポイントのURL。
            method (str): HTTPメソッド（例: "GET", "POST", "PUT"）。
            data (Optional[Dict[str, Any]]): リクエストボディとして送信するデータ（JSON）。

        Returns:
            Dict[str, Any]: APIからのJSONレスポンス。

        Raises:
            requests.exceptions.RequestException: ネットワークエラーやHTTPエラーステータスの場合。
        """
        try:
            response = requests.request(method, url, json=data, timeout=15)
            response.raise_for_status()  # 2xx以外のステータスコードで例外を発生させる
            return response.json()
        except requests.exceptions.RequestException as e:
            # 実際には、より堅牢なロギング機構を導入することが望ましい
            print(f"API request to {url} failed: {e}")
            raise

    @staticmethod
    def handle_api_response(response_json: Dict[str, Any]) -> Any:
        """APIレスポンスのJSONを解釈し、必要なデータを抽出または変換する。

        この関数は、APIの仕様に応じて具体的な処理を実装する必要がある。
        例えば、エラーレスポンスのハンドリングや、データモデルへの変換など。

        Args:
            response_json (Dict[str, Any]): APIから返されたパース済みのJSONデータ。

        Returns:
            Any: 処理済みのデータ。具体的な型はAPIレスポンスと後続の処理に依存する。
        """
        # この実装はダミーです。実際のAPIレスポンス形式に合わせて実装してください。
        if "error" in response_json and response_json["error"]:
            raise ValueError(f"API Error: {response_json['error']}")

        return response_json.get("data")
