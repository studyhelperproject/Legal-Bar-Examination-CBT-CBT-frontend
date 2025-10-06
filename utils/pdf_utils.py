# utils/pdf_utils.py
"""PDFのレンダリングや注釈の保存など、PDF操作に関連するユーティリティ機能を提供します。"""

import fitz  # PyMuPDF
from PyQt6.QtGui import QImage
from typing import List
from models.exam_text_models import Annotation

class PDFUtils:
    """PDF処理に関する共通機能を提供するユーティリティクラス。"""

    @staticmethod
    def render_page(page: fitz.Page, scale: float = 2.0) -> QImage:
        """PDFの指定されたページをQImageオブジェクトにレンダリングする。

        Args:
            page (fitz.Page): レンダリング対象のPyMuPDFページオブジェクト。
            scale (float): レンダリング時の拡大率。大きいほど高解像度になる。

        Returns:
            QImage: レンダリングされたページのQImageオブジェクト。
        """
        # 拡大率を指定してピクスマップを取得
        matrix = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=matrix)

        # QImageのフォーマットを決定
        if pix.alpha:
            image_format = QImage.Format.Format_RGBA8888
        else:
            image_format = QImage.Format.Format_RGB888

        # QImageオブジェクトを作成
        qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)

        # メモリリークを避けるため、データをコピーして返す
        return qimage.copy()

    @staticmethod
    def save_annotations_to_pdf(pdf_path: str, annotations: List[Annotation]) -> None:
        """注釈データを既存のPDFファイルに書き込む。

        この実装はダミーです。実際の注釈の種類（ペン、マーカーなど）に応じて、
        PyMuPDFのAPIを使用して図形やテキストをPDFページに追加する処理が必要です。

        Args:
            pdf_path (str): 注釈を保存するPDFファイルのパス。
            annotations (List[Annotation]): 保存する注釈のリスト。

        Raises:
            FileNotFoundError: 指定されたPDFファイルが存在しない場合。
            Exception: 保存処理中に予期せぬエラーが発生した場合。
        """
        try:
            doc = fitz.open(pdf_path)

            for annot_model in annotations:
                # ページ番号は0から始まるため、モデルのページ番号から1を引く
                page_index = annot_model.page - 1
                if 0 <= page_index < doc.page_count:
                    page = doc.load_page(page_index)

                    # 'data'の内容に応じて処理を分岐（ダミー実装）
                    if annot_model.type == 'marker' and 'rect' in annot_model.data:
                        rect = fitz.Rect(annot_model.data['rect'])
                        page.add_highlight_annot(rect)
                    elif annot_model.type == 'pen' and 'points' in annot_model.data:
                        ink_points = [fitz.Point(p) for p in annot_model.data['points']]
                        page.add_ink_annot([ink_points])

            # 変更を上書き保存
            doc.saveIncr()
        except FileNotFoundError:
            raise FileNotFoundError(f"PDFファイルが見つかりません: {pdf_path}")
        except Exception as e:
            raise Exception(f"注釈の保存中にエラーが発生しました: {e}")
        finally:
            if 'doc' in locals() and doc.is_open:
                doc.close()
