import os
import fitz
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog, QScrollArea, QWidget, QGridLayout, QToolButton, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter
from PyQt6.QtCore import Qt, QTimer, QPointF

class PDFHandler:
    def __init__(self, main_window):
        self.main = main_window
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.current_pdf_path = None
        self.page_overview_dialog = None
        self.spread_mode = False
        self.zoom_factor = 1.0
        self.MIN_ZOOM = 0.3
        self.MAX_ZOOM = 4.0
        self.fit_mode = None
        self._pending_page_render = None
        self._render_timer_active = False

    def open_pdf_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self.main, "PDF", "", "*.pdf")
        if not file_path:
            return

        file_name = os.path.basename(file_path)
        self.main.exam_type_label.setText(file_name)

        if self.page_overview_dialog:
            self.page_overview_dialog.close()

        self.main.annotation_handler.clear_selection()
        self.reset_zoom()

        # Reset view modes
        self.main.spread_toggle_action.blockSignals(True)
        self.main.spread_toggle_action.setChecked(False)
        self.main.spread_toggle_action.blockSignals(False)
        self.spread_mode = False

        self.main.scroll_toggle_action.blockSignals(True)
        self.main.scroll_toggle_action.setChecked(False)
        self.main.scroll_toggle_action.blockSignals(False)
        self._apply_scroll_settings_without_refresh(False)

        # Reset annotations and answers
        self.main.annotation_handler.clear_all_annotations()
        for i in range(self.main.answer_tab_widget.count()):
            sheet = self.main.answer_tab_widget.widget(i)
            sheet.set_page_texts([''] * sheet.TOTAL_PAGES)
            sheet.set_current_page(0)

        self.current_pdf_path = file_path
        try:
            self.pdf_document = fitz.open(file_path)
            self.total_pages = len(self.pdf_document)
            self.current_page = 0
            self.show_page(self.current_page)
        except Exception as e:
            QMessageBox.critical(self.main, "PDFエラー", f"PDFファイルを開けませんでした: {e}")
            self.pdf_document = None
            return

        self.main.history_handler.clear_history()
        self.main.history_handler.register_snapshot()
        self.main.update_char_count()

    def show_page(self, page_number):
        if not self.pdf_document or not (0 <= page_number < self.total_pages):
            return

        self.current_page = page_number
        self.main.annotation_handler.update_annotations_visibility()

        page = self.pdf_document.load_page(page_number)
        page_rect = page.rect

        viewport = self.main.pdf_scroll_area.viewport()
        if not viewport or viewport.width() <= 0 or viewport.height() <= 0:
            self._pending_page_render = page_number
            if not self._render_timer_active:
                self._render_timer_active = True
                QTimer.singleShot(0, self._retry_show_page)
            return

        label_width = viewport.width()
        label_height = viewport.height()

        if self.fit_mode == 'width':
            scale = label_width / page_rect.width if page_rect.width else 1.0
        elif self.fit_mode == 'height':
            scale = label_height / page_rect.height if page_rect.height else 1.0
        else:
            if self.spread_mode and not self.main.scroll_toggle_action.isChecked():
                effective_width = max(1, label_width - 20)
                width_per_page = effective_width / 2
                scale_x = width_per_page / page_rect.width if page_rect.width else 1.0
            else:
                scale_x = label_width / page_rect.width if page_rect.width else 1.0
            scale_y = label_height / page_rect.height if page_rect.height else 1.0
            scale = min(scale_x, scale_y)

        fit_scale = max(0.1, scale) * self.zoom_factor

        window_handle = self.main.windowHandle()
        dpr = float(window_handle.devicePixelRatio()) if window_handle else 1.0

        primary_image = self._render_page_image(page, fit_scale, dpr)

        if self.spread_mode and not self.main.scroll_toggle_action.isChecked() and page_number + 1 < self.total_pages:
            right_page = self.pdf_document.load_page(page_number + 1)
            right_image = self._render_page_image(right_page, fit_scale, dpr)
            combined_image = self._compose_spread_image(primary_image, right_image, dpr)
            pixmap = QPixmap.fromImage(combined_image)
        else:
            pixmap = QPixmap.fromImage(primary_image)

        pixmap.setDevicePixelRatio(dpr)
        self.main.pdf_display_label.setPixmap(pixmap)
        self.main.pdf_display_label.adjustSize()
        self.main.pdf_display_label._clamp_all_annotations()

        self.main.page_label.setText(f"{self.current_page + 1} / {self.total_pages}")
        self.main.page_num_input.setText(str(self.current_page + 1))

        self._pending_page_render = None
        self.main.annotation_handler.update_annotations_visibility()

        # Center the view
        hbar = self.main.pdf_scroll_area.horizontalScrollBar()
        vbar = self.main.pdf_scroll_area.verticalScrollBar()
        h_offset = max(0, (self.main.pdf_display_label.width() - viewport.width()) // 2)
        v_offset = 0 if self.fit_mode == 'height' else max(0, (self.main.pdf_display_label.height() - viewport.height()) // 2)
        hbar.setValue(h_offset)
        vbar.setValue(v_offset)

    def _retry_show_page(self):
        self._render_timer_active = False
        if self._pending_page_render is not None:
            page_number = self._pending_page_render
            self._pending_page_render = None
            self.show_page(page_number)

    def show_prev_page(self):
        self.show_page(self.current_page - 1)

    def show_next_page(self):
        self.show_page(self.current_page + 1)

    def goto_page_from_input(self):
        try:
            page_num = int(self.main.page_num_input.text()) - 1
            if 0 <= page_num < self.total_pages:
                self.show_page(page_num)
        except ValueError:
            pass

    def adjust_zoom(self, multiplier):
        new_zoom = self.zoom_factor * multiplier
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        if abs(new_zoom - self.zoom_factor) < 0.01:
            return
        self.fit_mode = None
        self.zoom_factor = new_zoom
        if self.pdf_document:
            self.show_page(self.current_page)
            if not self.main.history_handler.is_restoring():
                self.main.history_handler.register_snapshot()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.fit_mode = None

    def fit_to_height(self):
        if not self.pdf_document: return
        self.fit_mode = 'height'
        self.zoom_factor = 1.0
        self.show_page(self.current_page)
        if not self.main.history_handler.is_restoring():
            self.main.history_handler.register_snapshot()

    def fit_to_width(self):
        if not self.pdf_document: return
        self.fit_mode = 'width'
        self.zoom_factor = 1.0
        self.show_page(self.current_page)
        if not self.main.history_handler.is_restoring():
            self.main.history_handler.register_snapshot()

    def toggle_scroll_mode(self, horizontal_mode):
        if horizontal_mode and self.spread_mode:
            QMessageBox.information(self.main, "スクロール", "横スクロールでは見開き表示を利用できません。")
        self._apply_scroll_settings_without_refresh(horizontal_mode)
        if self.pdf_document:
            self.show_page(self.current_page)
            if not self.main.history_handler.is_restoring():
                self.main.history_handler.register_snapshot()

    def _apply_scroll_settings_without_refresh(self, horizontal_mode):
        scroll_area = self.main.pdf_scroll_area
        if not scroll_area: return

        if horizontal_mode:
            scroll_area.setWidgetResizable(False)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.spread_mode:
                self.spread_mode = False
                self.main.spread_toggle_action.blockSignals(True)
                self.main.spread_toggle_action.setChecked(False)
                self.main.spread_toggle_action.blockSignals(False)
            self.main.spread_toggle_action.setEnabled(False)
        else:
            scroll_area.setWidgetResizable(False)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.main.spread_toggle_action.setEnabled(True)

    def toggle_spread_mode(self, enabled):
        if enabled and self.main.scroll_toggle_action.isChecked():
            QMessageBox.information(self.main, "見開き", "横スクロール中は見開きを利用できません。")
            self.main.spread_toggle_action.blockSignals(True)
            self.main.spread_toggle_action.setChecked(False)
            self.main.spread_toggle_action.blockSignals(False)
            enabled = False

        self.spread_mode = enabled
        if self.pdf_document:
            if self.spread_mode and self.current_page >= self.total_pages:
                self.current_page = max(0, self.total_pages - 1)
            self.show_page(self.current_page)
            if not self.main.history_handler.is_restoring():
                self.main.history_handler.register_snapshot()

    def show_page_overview(self):
        if not self.pdf_document:
            QMessageBox.warning(self.main, "目次", "PDFファイルが開かれていません。")
            return

        if self.page_overview_dialog:
            self.page_overview_dialog.close()
            self.page_overview_dialog.deleteLater()
            self.page_overview_dialog = None

        dialog = QDialog(self.main)
        dialog.setWindowTitle("問題 目次")
        dialog.resize(960, 720)

        scroll_area = QScrollArea(dialog)
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        grid_layout = QGridLayout(container)
        grid_layout.setContentsMargins(16, 16, 16, 16)
        grid_layout.setSpacing(18)

        columns = 3
        thumb_width = 220
        for index in range(self.total_pages):
            thumb = self._render_page_thumbnail(index, thumb_width)
            button = QToolButton()
            button.setIcon(QIcon(thumb))
            button.setIconSize(thumb.size())
            button.setText(f"ページ {index + 1}")
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _, p=index: self._handle_page_overview_click(p))
            row, col = divmod(index, columns)
            grid_layout.addWidget(button, row, col)

        scroll_area.setWidget(container)
        layout = QVBoxLayout(dialog)
        layout.addWidget(scroll_area)
        dialog.setLayout(layout)
        dialog.finished.connect(self._clear_page_overview_dialog)
        self.page_overview_dialog = dialog
        dialog.show()

    def _handle_page_overview_click(self, page_number):
        self.show_page(page_number)
        if self.page_overview_dialog:
            self.page_overview_dialog.close()

    def _clear_page_overview_dialog(self, *_):
        if self.page_overview_dialog:
            self.page_overview_dialog.deleteLater()
            self.page_overview_dialog = None

    def _render_page_image(self, page, scale, dpr):
        mat = fitz.Matrix(scale * dpr, scale * dpr)
        pix = page.get_pixmap(matrix=mat, annots=True)
        image_format = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        return QImage(pix.samples, pix.width, pix.height, pix.stride, image_format).copy()

    def _compose_spread_image(self, left_image, right_image, dpr, gap_px=20):
        if right_image is None:
            return left_image
        gap = int(gap_px * dpr)
        width = left_image.width() + right_image.width() + gap
        height = max(left_image.height(), right_image.height())
        combined = QImage(width, height, QImage.Format.Format_RGBA8888)
        combined.fill(Qt.GlobalColor.white)
        painter = QPainter(combined)
        painter.drawImage(0, 0, left_image)
        painter.drawImage(left_image.width() + gap, 0, right_image)
        painter.end()
        return combined

    def _render_page_thumbnail(self, page_number, target_width):
        page = self.pdf_document.load_page(page_number)
        rect = page.rect
        scale = target_width / rect.width if rect.width else 1.0
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, annots=False)
        image_format = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format).copy()
        return QPixmap.fromImage(image)

    def handle_resize_event(self):
        if self.pdf_document:
            self._pending_page_render = self.current_page
            if not self._render_timer_active:
                self._render_timer_active = True
                QTimer.singleShot(0, self._retry_show_page)