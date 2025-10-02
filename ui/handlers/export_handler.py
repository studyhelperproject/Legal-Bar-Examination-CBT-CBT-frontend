import os
import json
from datetime import datetime
import fitz

from docx import Document
from docx.shared import Cm, Pt
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import QFont, QFontInfo, QPainter, QImage, QColor
from PyQt6.QtCore import QMarginsF, QPointF, QRectF, QSizeF
from PyQt6.QtPrintSupport import QPrinter

from ui.widgets import ANSWER_TEMPLATE_PATH

class ExportHandler:
    def __init__(self, main_window):
        self.main = main_window
        self._template_image_cache = {}

    def save_as_word(self):
        current_sheet = self.main.answer_tab_widget.currentWidget()
        if not current_sheet:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"answer_{timestamp}.docx"
        initial_path = os.path.join(os.path.expanduser("~"), default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self.main, "Word形式で保存", initial_path, "Word Documents (*.docx)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith('.docx'):
            file_path += '.docx'

        try:
            self._export_sheet_to_docx(current_sheet, file_path)
            QMessageBox.information(self.main, "保存完了", f"答案をWord形式で保存しました。\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self.main, "保存エラー", f"Wordファイルの保存に失敗しました。\n{exc}")

    def save_as_pdf(self):
        current_sheet = self.main.answer_tab_widget.currentWidget()
        if not current_sheet:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"answer_{timestamp}.pdf"
        initial_path = os.path.join(os.path.expanduser("~"), default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self.main, "PDF形式で保存", initial_path, "PDF Files (*.pdf)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith('.pdf'):
            file_path += '.pdf'

        try:
            self._export_sheet_to_pdf(current_sheet, file_path)
            QMessageBox.information(self.main, "保存完了", f"答案をPDF形式で保存しました。\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self.main, "保存エラー", f"PDFファイルの保存に失敗しました。\n{exc}")

    def _export_sheet_to_docx(self, sheet, file_path):
        page_texts = self._sheet_page_texts(sheet)
        doc = Document()
        section = doc.sections[0]
        section.page_width, section.page_height = Cm(21.0), Cm(29.7)
        section.left_margin, section.right_margin = Cm(2.0), Cm(2.0)
        section.top_margin, section.bottom_margin = Cm(2.0), Cm(2.0)

        style = doc.styles['Normal']
        style.font.name = 'MS Mincho'
        style.font.size = Pt(12)
        style._element.rPr.rFonts.set(qn('w:eastAsia'), 'MS Mincho')

        for page_index, page_text in enumerate(page_texts):
            lines = self._page_lines_for_export(page_text)

            table = doc.add_table(rows=23, cols=2)
            table.style = 'Table Grid'
            table.autofit = False

            line_col = table.columns[0]
            text_col = table.columns[1]
            line_width = Cm(1.0)
            line_col.width = line_width
            text_col.width = section.page_width - section.left_margin - section.right_margin - line_width

            for row_idx, row in enumerate(table.rows):
                line_cell, text_cell = row.cells[0], row.cells[1]

                line_para = line_cell.paragraphs[0]
                line_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                line_para.add_run(f"{row_idx + 1:02}")

                text_para = text_cell.paragraphs[0]
                text_para.add_run(lines[row_idx] if row_idx < len(lines) else '')

            if page_index < len(page_texts) - 1:
                doc.add_page_break()

        doc.save(file_path)

    def _export_sheet_to_pdf(self, sheet, file_path):
        page_texts = self._sheet_page_texts(sheet)
        if not page_texts: page_texts = ['']

        font = QFont("Hiragino Mincho ProN", 12)
        if not QFontInfo(font).exactMatch(): font = QFont("MS Mincho", 12)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPrinter.PageSize.A4)
        printer.setPageMargins(QMarginsF(20, 20, 20, 25), QPageLayout.Unit.Millimeter)

        painter = QPainter(printer)
        painter.setFont(font)
        metrics = painter.fontMetrics()

        max_lines, max_chars = (sheet.pages[0].max_lines, sheet.pages[0].max_chars) if sheet.pages else (23, 30)
        line_height = metrics.lineSpacing()

        page_rect = printer.pageRect(QPrinter.Unit.Point)
        template_image = self._get_template_image(printer.resolution())

        for i, page_text in enumerate(page_texts):
            if i > 0: printer.newPage()

            if not template_image.isNull():
                painter.drawImage(page_rect, template_image)

            lines = self._page_lines_for_export(page_text, max_lines, max_chars)
            # This part would need more complex layouting to match the original if it drew lines/boxes.
            # For now, just printing the text.
            for row, line in enumerate(lines):
                painter.drawText(QPointF(100, 100 + row * line_height), line)

            painter.drawText(QRectF(page_rect), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, f"{i + 1} / {len(page_texts)}")

        painter.end()

    def _sheet_page_texts(self, sheet):
        texts = sheet.get_page_texts()
        last_nonempty = -1
        for idx, text in enumerate(texts):
            if text.strip():
                last_nonempty = idx
        return texts[:last_nonempty + 1] if last_nonempty != -1 else ([''] if not texts else [texts[0]])

    def _page_lines_for_export(self, text, max_lines=23, max_chars=30):
        lines = []
        for raw_line in (text.split('\n') if text else ['']):
            for i in range(0, len(raw_line), max_chars):
                lines.append(raw_line[i:i+max_chars])
        return lines[:max_lines]

    def _get_template_image(self, dpi):
        if dpi in self._template_image_cache:
            return self._template_image_cache[dpi]

        image = QImage()
        if ANSWER_TEMPLATE_PATH and os.path.exists(ANSWER_TEMPLATE_PATH):
            try:
                doc = fitz.open(ANSWER_TEMPLATE_PATH)
                page = doc.load_page(0)
                mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                image.loadFromData(pix.tobytes("png"), "PNG")
            except Exception:
                pass # Failed to load template

        self._template_image_cache[dpi] = image
        return image

    def save_session_via_dialog(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"cbt_session_{timestamp}.json"
        initial_path = os.path.join(os.path.expanduser("~"), default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self.main, "セッションの保存", initial_path, "CBTセッション (*.json);;All Files (*)"
        )
        if not file_path:
            return False

        try:
            data = self.main.history_handler.serialize_full_session()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self.main, "保存完了", f"セッションを保存しました。\n{file_path}")
            return True
        except Exception as exc:
            QMessageBox.critical(self.main, "保存エラー", f"セッションの保存に失敗しました。\n{exc}")
            return False