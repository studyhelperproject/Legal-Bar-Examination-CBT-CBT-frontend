# utils/law_utils.py
import xml.etree.ElementTree as ET
from typing import Dict, Any, Text

class LawUtils:
    """法令のデータ処理（XML解析、整形）に関連するユーティリティクラス。"""

    @staticmethod
    def parse_law_xml(xml_content: str) -> Dict[str, Any]:
        """e-Govから取得した法令のXMLデータを解析し、主要な情報を辞書として抽出する。

        この実装は基本的な構造をパースするダミーです。
        実際の法令XMLの複雑な構造に合わせて、より詳細なパース処理が必要です。

        Args:
            xml_content (str): 解析対象の法令XMLデータ文字列。

        Returns:
            Dict[str, Any]: 法令名、法令番号、条文などの情報を含む辞書。

        Raises:
            ET.ParseError: XMLのパースに失敗した場合。
        """
        try:
            root = ET.fromstring(xml_content)
            # これはダミーの実装です。実際のXML構造に合わせてキーと値を取得する必要があります。
            law_title_element = root.find('.//LawTitle')
            law_title = law_title_element.text if law_title_element is not None else ''

            law_num_element = root.find('.//LawNum')
            law_num = law_num_element.text if law_num_element is not None else ''

            articles = []
            for article in root.findall('.//Article'):
                article_title_element = article.find('ArticleTitle')
                article_title = article_title_element.text if article_title_element is not None else ''
                paragraphs = [
                    p.text for p in article.findall('.//ParagraphSentence/Sentence')
                    if p.text is not None
                ]
                articles.append({'title': article_title, 'paragraphs': paragraphs})

            return {
                'title': law_title,
                'number': law_num,
                'articles': articles,
            }
        except ET.ParseError as e:
            print(f"XML parse error: {e}")
            raise

    @staticmethod
    def format_law_content(parsed_data: Dict[str, Any]) -> Text:
        """解析済みの法令データを、表示用に整形されたテキストに変換する。

        Args:
            parsed_data (Dict[str, Any]): `parse_law_xml`によって生成された辞書データ。

        Returns:
            Text: 表示用に整形された法令の文字列。
        """
        # この実装はダミーです。
        lines = [
            f"法令名: {parsed_data.get('title', 'N/A')}",
            f"法令番号: {parsed_data.get('number', 'N/A')}",
            "---"
        ]
        for article in parsed_data.get('articles', []):
            lines.append(article.get('title', ''))
            for i, paragraph in enumerate(article.get('paragraphs', []), 1):
                lines.append(f"  {i}. {paragraph}")
            lines.append("")

        return "\n".join(lines)
