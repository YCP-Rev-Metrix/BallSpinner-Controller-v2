import os
import re

from PyQt6 import QtWidgets
from PyQt6.QtCore import QUrl


class HelpDialog(QtWidgets.QDialog):
    _FRONTMATTER_RE = re.compile(r"\A\+\+\+\s*\n(.*?)\n\+\+\+\s*\n", re.DOTALL)
    _SHORTCODE_RE = re.compile(r"\{\{[%<].*?[%>]\}\}", re.DOTALL)
    _IMG_QUERY_RE = re.compile(r"(!\[[^\]]*\]\([^)?\s]+)\?[^)\s]*(\))")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Page Help")
        self.resize(1100, 720)
        self.setModal(False)

        self._help_root = os.path.join(os.path.dirname(__file__), "help")
        self._items_by_key = {}
        self._suspend_selection_handler = False

        # Sidebar hierarchy: main pages top-level, widget docs as subpages.
        self._pages = [
            (
                "home",
                "Home",
                [
                    ("before_you_start", "Before You Start"),
                    ("sample_shot_session", "Sample Shot Session"),
                ],
            ),
            (
                "diagnostic_mode",
                "Diagnostic Mode",
                [
                    ("smartdot_connect_widget", "SmartDot Connect Widget"),
                    ("smartdot_general", "General SmartDot Help"),
                ],
            ),
            (
                "shot_mode",
                "Shot Mode",
                [
                    ("smartdot_connect_widget", "SmartDot Connect Widget"),
                    ("input_graph_widget", "Input Graph Widget"),
                ],
            ),
            (
                "shot_view",
                "Shot View",
                [
                    ("motor_graph_widget", "Motor and SmartDot Graph Widget"),
                ],
            ),
            (
                "analysis_mode",
                "Analysis Mode",
                [
                    ("motor_graph_widget", "Motor and SmartDot Graph Widget"),
                    ("wavelet_dialog", "Wavelet Dialog"),
                ],
            ),
            (
                "data_view",
                "Data View",
                [
                    ("sample_shot_session", "Sample Shot Session"),
                ],
            ),
            ("cloud_test", "Cloud Test", []),
        ]

        self._build_ui()
        self._populate_page_list()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(4)
        self.lblTitle = QtWidgets.QLabel("Help")
        self.lblTitle.setStyleSheet("font-weight: bold;")
        self.lblTitle.setMaximumHeight(24)
        toolbar.addWidget(self.lblTitle)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QtWidgets.QSplitter(self)
        self.treePages = QtWidgets.QTreeWidget(splitter)
        self.treePages.setHeaderHidden(True)
        self.treePages.setMinimumWidth(280)
        self.viewer = QtWidgets.QTextBrowser(splitter)
        self.viewer.setOpenExternalLinks(False)
        self.viewer.setOpenLinks(False)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([290, 810])
        layout.addWidget(splitter)

        self.treePages.currentItemChanged.connect(self._on_current_item_changed)
        self.viewer.anchorClicked.connect(self._on_anchor_clicked)

    def _populate_page_list(self):
        self.treePages.clear()
        self._items_by_key.clear()
        for key, title, subpages in self._pages:
            parent_item = QtWidgets.QTreeWidgetItem([title])
            parent_item.setData(0, 0x0100, key)
            self.treePages.addTopLevelItem(parent_item)
            self._items_by_key[key] = parent_item
            for child_key, child_title in subpages:
                child_item = QtWidgets.QTreeWidgetItem([child_title])
                child_item.setData(0, 0x0100, child_key)
                parent_item.addChild(child_item)
                self._items_by_key[child_key] = child_item
            parent_item.setExpanded(False)

    def _parse_frontmatter(self, text):
        metadata = {}
        match = self._FRONTMATTER_RE.match(text)
        if not match:
            return metadata, text

        raw_frontmatter = match.group(1)
        for line in raw_frontmatter.splitlines():
            if "=" not in line:
                continue
            name, _, value = line.partition("=")
            metadata[name.strip()] = value.strip().strip('"').strip("'")
        return metadata, text[match.end() :]

    def _preprocess_markdown(self, raw_text):
        metadata, content = self._parse_frontmatter(raw_text)
        content = self._SHORTCODE_RE.sub("", content)
        content = self._IMG_QUERY_RE.sub(r"\1\2", content)
        title = metadata.get("title")
        if title:
            content = f"# {title}\n\n{content}"
        return content, metadata

    def _help_file_for_key(self, key):
        return os.path.join(self._help_root, key, "_index.md")

    def _load_page(self, key):
        path = self._help_file_for_key(key)
        if not os.path.exists(path):
            self.viewer.setMarkdown(f"# Missing help page\n\nNo file found for `{key}`.")
            self.lblTitle.setText("Help")
            return

        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw = handle.read()
        except Exception as exc:
            self.viewer.setMarkdown(f"# Help load error\n\nCould not read `{key}`.\n\n{exc}")
            self.lblTitle.setText("Help")
            return

        rendered, metadata = self._preprocess_markdown(raw)
        page_dir = os.path.dirname(path)
        self.viewer.setSearchPaths([page_dir, self._help_root])
        self.viewer.setMarkdown(rendered)
        self.lblTitle.setText(metadata.get("title", "Help"))

    def _on_current_item_changed(self, item, _previous):
        if self._suspend_selection_handler:
            return
        if item is None:
            return
        key = item.data(0, 0x0100)
        if not key:
            return
        if item.childCount() > 0:
            item.setExpanded(True)
        self._load_page(key)

    def _url_to_key(self, url):
        path = url.path() or ""
        parts = [part for part in path.split("/") if part and part != ".."]
        if not parts:
            return None
        if parts[-1] == "_index.md":
            parts = parts[:-1]
            if not parts:
                return None
        candidate = parts[-1]
        return candidate if candidate in self._items_by_key else None

    def _on_anchor_clicked(self, url: QUrl):
        key = self._url_to_key(url)
        if key is None:
            return
        self.show_page(key)

    def show_page(self, key):
        item = self._items_by_key.get(key)
        if item is None:
            return
        if self.treePages.currentItem() is item:
            self._load_page(key)
            return
        parent = item.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        self.treePages.setCurrentItem(item)

