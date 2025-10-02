# services/exam_text_service.py
import fitz  # PyMuPDF
import json
from .base_service import BaseService
from models.exam_text_models import PDFDocument, Annotation
from typing import List, Optional

class ExamTextService(BaseService[PDFDocument]):
    """問題文（PDF）とその注釈データを管理するサービスクラス。

    PDFの読み込み、注釈の保存・読み込みなど、問題文に関連するビジネスロジックを実装します。
    """

    def __init__(self, storage_service: Optional['StorageService'] = None) -> None:
        """ExamTextServiceのコンストラクタ。

        Args:
            storage_service (Optional[StorageService]): データ永続化のためのストレージサービス。
        """
        super().__init__(storage_service=storage_service)

    def load_pdf(self, file_path: str) -> Optional[PDFDocument]:
        """指定されたパスからPDFファイルを読み込み、PDFDocumentオブジェクトを生成する。

        Args:
            file_path (str): 読み込むPDFファイルのパス。

        Returns:
            Optional[PDFDocument]: 読み込まれたPDF文書データ。ファイルが存在しない場合はNone。
        """
        try:
            doc = fitz.open(file_path)
            annotations = self.load_annotations(file_path)
            pdf_document = PDFDocument(
                file_path=file_path,
                total_pages=doc.page_count,
                current_page=1,
                annotations=annotations
            )
            doc.close()
            return pdf_document
        except FileNotFoundError:
            return None

    def save_annotations(self, file_path: str, annotations: List[Annotation]) -> None:
        """注釈リストをJSONファイルとして永続化する。

        注釈はPDF自体ではなく、関連付けられた別ファイルに保存されます。

        Args:
            file_path (str): 元のPDFファイルのパス。注釈ファイルの名前の基になる。
            annotations (List[Annotation]): 保存する注釈のリスト。
        """
        if self.storage_service:
            annotation_path = f"{file_path}.annotations.json"
            # Annotationオブジェクトを辞書に変換して保存
            annot_data = [annot.__dict__ for annot in annotations]
            self.storage_service.save_json(annotation_path, annot_data)
            print(f"注釈を {annotation_path} に保存しました。")

    def load_annotations(self, file_path: str) -> List[Annotation]:
        """JSONファイルから注釈リストを読み込む。

        Args:
            file_path (str): 元のPDFファイルのパス。

        Returns:
            List[Annotation]: 読み込まれた注釈のリスト。ファイルが存在しない場合は空リスト。
        """
        if self.storage_service:
            annotation_path = f"{file_path}.annotations.json"
            annot_data = self.storage_service.load_json(annotation_path)
            if annot_data:
                # 辞書からAnnotationオブジェクトに変換
                return [Annotation(**data) for data in annot_data]
        return []

    def load_data(self, identifier: str) -> Optional[PDFDocument]:
        """BaseServiceから継承したメソッド。PDFデータを読み込む。

        Args:
            identifier (str): 読み込むPDFのファイルパス。

        Returns:
            Optional[PDFDocument]: 読み込まれたPDF文書データ。
        """
        return self.load_pdf(identifier)

    def save_data(self, data: PDFDocument) -> None:
        """BaseServiceから継承したメソッド。PDFに関連するデータ（注釈）を保存する。

        Args:
            data (PDFDocument): 保存するデータを含むPDFDocumentオブジェクト。
        """
        self.save_annotations(data.file_path, data.annotations)
