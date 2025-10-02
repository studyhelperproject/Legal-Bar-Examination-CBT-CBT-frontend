from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QLineEdit, QTextBrowser, QMessageBox, QDialog, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor

from utils.constants import LAW_DATA
from utils.law_fetcher import LawFetcherThread
from utils.xml_parser import parse_law_xml_to_html

class LawHandler:
    def __init__(self, main_window):
        self.main = main_window
        self.law_fetcher_thread = None
        self.law_bookmarks = []

    def populate_law_tree(self):
        tree = self.main.law_toc_tree
        tree.clear()
        for subject, laws in LAW_DATA.items():
            subject_item = QTreeWidgetItem(tree, [subject])
            for law_name, law_id in laws.items():
                law_item = QTreeWidgetItem(subject_item, [law_name])
                law_item.setData(0, Qt.ItemDataRole.UserRole, law_id)
        tree.expandAll()

    def on_law_tree_selection_changed(self, current, _):
        if not current: return
        law_id = current.data(0, Qt.ItemDataRole.UserRole)
        if law_id:
            self.fetch_law_data(current.text(0), law_id)

    def fetch_law_data(self, law_name, law_id):
        if not law_id:
            self.main.law_main_area.setText("法令を選択してください。")
            return

        self.main.law_main_area.setText(f"{law_name}のデータを取得中...")
        if self.law_fetcher_thread and self.law_fetcher_thread.isRunning():
            self.law_fetcher_thread.terminate()
            self.law_fetcher_thread.wait()

        self.law_fetcher_thread = LawFetcherThread(law_id, self.main)
        self.law_fetcher_thread.result_ready.connect(self.on_law_data_ready)
        self.law_fetcher_thread.error_occurred.connect(self.on_law_data_error)
        self.law_fetcher_thread.start()

    def on_law_data_ready(self, result_tuple):
        xml_string = result_tuple[0]
        _, main_html = parse_law_xml_to_html(xml_string)
        self.main.law_main_area.setHtml(main_html)

    def on_law_data_error(self, error_message):
        self.main.law_main_area.setText(error_message)

    def filter_law_tree(self, text):
        root = self.main.law_toc_tree.invisibleRootItem()
        for i in range(root.childCount()):
            subject_item = root.child(i)
            has_visible_child = False
            for j in range(subject_item.childCount()):
                law_item = subject_item.child(j)
                is_match = text.lower() in law_item.text(0).lower()
                law_item.setHidden(not is_match)
                if is_match:
                    has_visible_child = True
            subject_item.setHidden(not has_visible_child)
            if has_visible_child:
                subject_item.setExpanded(True)

    def toggle_law_toc_visibility(self, checked):
        self.main.law_toc_tree.setVisible(checked)
        self.main.toc_search_input.setVisible(checked)
        self.main.toc_button.setChecked(checked)
        self.main.toggle_toc_view_button.setChecked(checked)
        self.main.toggle_toc_view_button.setText("<" if checked else ">")

    def jump_to_article(self):
        article = self.main.article_jump_input.text().strip()
        para = self.main.paragraph_jump_input.text().strip()
        item = self.main.item_jump_input.text().strip()
        if not article: return

        anchor = f"article-{article}"
        if para: anchor += f"-{para}"
        if item: anchor += f"-{item}"
        self.main.law_main_area.scrollToAnchor(anchor)

    def search_in_law_text(self, text):
        self.main.law_main_area.find(text)

    def handle_law_bookmark_action(self):
        cursor = self.main.law_main_area.textCursor()
        if cursor and cursor.hasSelection():
            self._add_law_bookmark(cursor)
        else:
            self._show_law_bookmark_dialog()

    def _add_law_bookmark(self, cursor):
        text = cursor.selectedText().replace('\u2029', '\n').strip()
        if not text: return

        start, end = cursor.selectionStart(), cursor.selectionEnd()
        if any(b['start'] == start and b['end'] == end for b in self.law_bookmarks):
            QMessageBox.information(self.main, "付箋", "この選択範囲はすでに登録されています。")
            return

        self.law_bookmarks.append({
            'text': text,
            'snippet': text[:77] + '…' if len(text) > 80 else text,
            'start': start, 'end': end,
        })
        QMessageBox.information(self.main, "付箋", "選択した条文を付箋として登録しました。")

    def _show_law_bookmark_dialog(self):
        if not self.law_bookmarks:
            QMessageBox.information(self.main, "付箋", "登録された付箋はありません。")
            return

        dialog = QDialog(self.main)
        dialog.setWindowTitle("法令付箋一覧")
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        for i, bookmark in enumerate(self.law_bookmarks, 1):
            list_widget.addItem(f"{i}. {bookmark['snippet']}")

        show_btn = QPushButton("表示")
        delete_btn = QPushButton("削除")
        close_btn = QPushButton("閉じる")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(show_btn); btn_layout.addWidget(delete_btn)
        btn_layout.addStretch(); btn_layout.addWidget(close_btn)

        layout.addWidget(list_widget); layout.addLayout(btn_layout)

        def on_show():
            if list_widget.currentRow() >= 0:
                self._activate_law_bookmark(list_widget.currentRow())
                dialog.accept()

        def on_delete():
            row = list_widget.currentRow()
            if row >= 0:
                del self.law_bookmarks[row]
                list_widget.takeItem(row)
                if not self.law_bookmarks: dialog.accept()

        show_btn.clicked.connect(on_show)
        delete_btn.clicked.connect(on_delete)
        close_btn.clicked.connect(dialog.reject)
        list_widget.itemDoubleClicked.connect(on_show)

        dialog.exec()

    def _activate_law_bookmark(self, index):
        if not (0 <= index < len(self.law_bookmarks)): return
        bookmark = self.law_bookmarks[index]
        cursor = self.main.law_main_area.textCursor()
        cursor.setPosition(bookmark['start'])
        cursor.setPosition(bookmark['end'], QTextCursor.MoveMode.KeepAnchor)
        self.main.law_main_area.setTextCursor(cursor)
        self.main.law_main_area.ensureCursorVisible()