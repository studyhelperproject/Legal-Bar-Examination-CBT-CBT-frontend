import os

from .pdf_display import PDFDisplayLabel
from .annotations import TextAnnotationWidget, ShapeAnnotationWidget
from .answer_sheet import (
    AnswerGridEditor,
    AnswerGridBackground,
    AnswerSheetPageWidget,
    AnswerSheet,
)
from .memo import MemoWindow

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
ANSWER_TEMPLATE_PATH = os.path.join(ASSETS_DIR, "answer_template.pdf")

__all__ = [
    "PDFDisplayLabel",
    "TextAnnotationWidget",
    "ShapeAnnotationWidget",
    "AnswerGridEditor",
    "AnswerGridBackground",
    "AnswerSheetPageWidget",
    "AnswerSheet",
    "MemoWindow",
    "ANSWER_TEMPLATE_PATH",
]