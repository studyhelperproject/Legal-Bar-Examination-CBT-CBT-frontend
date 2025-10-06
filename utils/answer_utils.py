# utils/answer_utils.py
from models.answer_models import AnswerSheet
from typing import Text

class AnswerUtils:
    """答案に関連する共通処理や計算を行うユーティリティクラス。"""

    @staticmethod
    def count_characters(text: str) -> int:
        """指定されたテキストの文字数をカウントする。

        Args:
            text (str): 文字数を数える対象のテキスト。

        Returns:
            int: テキストの文字数。
        """
        # ここでは単純な文字数カウントを想定。要件に応じて変更が必要。
        return len(text)

    @staticmethod
    def format_answer_for_export(answer_data: AnswerSheet) -> Text:
        """答案データをエクスポート用のプレーンテキスト形式にフォーマットする。

        Args:
            answer_data (AnswerSheet): フォーマットする答案データ。

        Returns:
            Text: 整形された文字列。
        """
        # この実装はダミーです。実際のエクスポート形式に合わせて実装してください。
        export_lines = [f"問題番号: {answer_data.question_number}", "---"]
        for page in answer_data.pages:
            export_lines.append(f"【ページ {page.page_number}】")
            export_lines.append(page.content)
            export_lines.append("")
        return "\n".join(export_lines)
