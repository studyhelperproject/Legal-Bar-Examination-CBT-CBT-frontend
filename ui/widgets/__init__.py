import os

from .pdf_display import PDFDisplayLabel
from .text_annotation import TextAnnotationWidget
from .shape_annotation import ShapeAnnotationWidget
from .answer_sheet import AnswerSheet
from .answer_editor import AnswerGridEditor
from .answer_page import AnswerSheetPageWidget
from .memo import MemoWindow

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
ANSWER_TEMPLATE_PATH = os.path.join(ASSETS_DIR, "answer_template.pdf")

__all__ = [
    "PDFDisplayLabel",
    "TextAnnotationWidget",
    "ShapeAnnotationWidget",
    "AnswerGridEditor",
    "AnswerSheetPageWidget",
    "AnswerSheet",
    "MemoWindow",
    "ANSWER_TEMPLATE_PATH",
]