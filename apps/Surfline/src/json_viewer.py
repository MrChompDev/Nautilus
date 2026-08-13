"""
JSON / Structured Data Viewer
Renders application/json, application/xml, text/yaml
as interactive collapsible node trees.
"""
import json
import xml.etree.ElementTree as ET

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QLabel,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.Surfline.src.theme import COLORS, FONTS


class JsonTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Key", "Value", "Type"])
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(False)
        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 400)
        self.setColumnWidth(2, 80)
        self.setStyleSheet(f"""
            QTreeWidget {{
                background: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
                border: none;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 1px 4px;
                border-bottom: 1px solid {COLORS['border']}20;
            }}
            QTreeWidget::item:selected {{
                background: {COLORS['accent_darker']}40;
            }}
            QTreeWidget::item:hover {{
                background: {COLORS['bg_elevated']};
            }}
            QTreeWidget::branch {{
                background: {COLORS['bg_primary']};
            }}
            QHeaderView::section {{
                background: {COLORS['bg_secondary']};
                color: {COLORS['accent']};
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                border-right: 1px solid {COLORS['border']};
                padding: 4px 8px;
                font-weight: bold;
                font-size: {FONTS['size_sm']}px;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
            }}
        """)

    def populate(self, data, parent_item=None, key=None):
        if parent_item is None:
            parent_item = self.invisibleRootItem()

        if isinstance(data, dict):
            for k, v in data.items():
                item = QTreeWidgetItem()
                item.setText(0, str(k))
                if isinstance(v, (dict, list)):
                    item.setText(1, f"{{{len(v)} items}}" if isinstance(v, dict) else f"[{len(v)} items]")
                    item.setText(2, type(v).__name__)
                    item.setForeground(0, QColor(COLORS['accent']))
                    item.setForeground(2, QColor(COLORS['text_muted']))
                    parent_item.addChild(item)
                    self.populate(v, item, k)
                else:
                    item.setText(1, self._truncate(str(v), 200))
                    item.setText(2, self._type_name(v))
                    item.setForeground(0, QColor(COLORS['text_primary']))
                    item.setForeground(1, QColor(COLORS['text_secondary']))
                    item.setForeground(2, QColor(COLORS['text_muted']))
                    parent_item.addChild(item)
        elif isinstance(data, list):
            for i, v in enumerate(data):
                item = QTreeWidgetItem()
                item.setText(0, f"[{i}]")
                if isinstance(v, (dict, list)):
                    item.setText(1, f"{{{len(v)} items}}" if isinstance(v, dict) else f"[{len(v)} items]")
                    item.setText(2, type(v).__name__)
                    item.setForeground(0, QColor(COLORS['warning']))
                    item.setForeground(2, QColor(COLORS['text_muted']))
                    parent_item.addChild(item)
                    self.populate(v, item, str(i))
                else:
                    item.setText(1, self._truncate(str(v), 200))
                    item.setText(2, self._type_name(v))
                    item.setForeground(0, QColor(COLORS['warning']))
                    item.setForeground(1, QColor(COLORS['text_secondary']))
                    item.setForeground(2, QColor(COLORS['text_muted']))
                    parent_item.addChild(item)
        else:
            item = QTreeWidgetItem()
            item.setText(0, str(key) if key else "")
            item.setText(1, self._truncate(str(data), 200))
            item.setText(2, self._type_name(data))
            parent_item.addChild(item)

    def _truncate(self, s, maxlen):
        s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        if len(s) > maxlen:
            return s[:maxlen] + "..."
        return s

    def _type_name(self, val):
        if val is None:
            return "null"
        if isinstance(val, bool):
            return "bool"
        if isinstance(val, int):
            return "int"
        if isinstance(val, float):
            return "float"
        return "str"


class StructuredDataViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {COLORS['bg_primary']};
            }}
            QTabBar::tab {{
                background: {COLORS['tab_inactive']};
                color: {COLORS['text_secondary']};
                padding: 4px 12px;
                border: none;
                border-bottom: 2px solid transparent;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['tab_active']};
                color: {COLORS['accent']};
                border-bottom: 2px solid {COLORS['accent']};
            }}
        """)

        self.tree_tab = QWidget()
        tree_layout = QVBoxLayout(self.tree_tab)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        self.tree = JsonTreeWidget()
        tree_layout.addWidget(self.tree)
        self.tabs.addTab(self.tree_tab, "Tree View")

        self.raw_tab = QWidget()
        raw_layout = QVBoxLayout(self.raw_tab)
        raw_layout.setContentsMargins(0, 0, 0, 0)
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
                border: none;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 8px;
                selection-background-color: {COLORS['selection']};
            }}
        """)
        raw_layout.addWidget(self.raw_text)
        self.tabs.addTab(self.raw_tab, "Raw")

        layout.addWidget(self.tabs)

        self.info_bar = QLabel("No data loaded")
        self.info_bar.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                background: {COLORS['bg_secondary']};
                border-top: 1px solid {COLORS['border']};
                padding: 2px 8px;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
            }}
        """)
        layout.addWidget(self.info_bar)

    def load_data(self, raw_content: str, mime_type: str = ""):
        self.raw_text.setPlainText(raw_content)

        parsed = None
        data_type = ""

        if mime_type == "application/json" or self._looks_like_json(raw_content):
            data_type = "JSON"
            try:
                parsed = json.loads(raw_content)
                self.info_bar.setText(
                    f"Type: JSON | Size: {len(raw_content)} bytes | "
                    f"Root: {type(parsed).__name__}"
                )
            except json.JSONDecodeError as e:
                self.info_bar.setText(f"JSON Parse Error: {e}")
                return
        elif mime_type in ("text/xml", "application/xml") or self._looks_like_xml(raw_content):
            data_type = "XML"
            try:
                root = ET.fromstring(raw_content)
                parsed = self._xml_to_dict(root)
                self.info_bar.setText(
                    f"Type: XML | Size: {len(raw_content)} bytes | "
                    f"Root: <{root.tag}>"
                )
            except ET.ParseError as e:
                self.info_bar.setText(f"XML Parse Error: {e}")
                return
        elif mime_type == "text/yaml" or self._looks_like_yaml(raw_content):
            data_type = "YAML"
            try:
                import yaml
                parsed = yaml.safe_load(raw_content)
                self.info_bar.setText(
                    f"Type: YAML | Size: {len(raw_content)} bytes | "
                    f"Root: {type(parsed).__name__}"
                )
            except Exception as e:
                self.info_bar.setText(f"YAML Parse Error: {e}")
                return
        else:
            self.info_bar.setText(
                f"Content-Type: {mime_type or 'unknown'} | "
                f"Size: {len(raw_content)} bytes"
            )
            self.tree.clear()
            return

        self.tree.clear()
        if parsed is not None:
            self.tree.populate(parsed)
            self.tree.expandToDepth(1)
            self.tabs.setTabText(0, f"Tree View ({data_type})")
            self.tabs.setTabText(1, f"Raw ({data_type})")

    def _looks_like_json(self, text):
        t = text.strip()
        return (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]"))

    def _looks_like_xml(self, text):
        t = text.strip()
        return t.startswith("<") and t.endswith(">")

    def _looks_like_yaml(self, text):
        t = text.strip()
        if not t:
            return False
        first_line = t.split("\n")[0].strip()
        return ":" in first_line and not first_line.startswith("{") and not first_line.startswith("<")

    def _xml_to_dict(self, element):
        result = {}
        result["@tag"] = element.tag
        if element.attrib:
            result["@attributes"] = dict(element.attrib)
        if element.text and element.text.strip():
            result["@text"] = element.text.strip()
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_data = self._xml_to_dict(child)
                tag = child.tag
                if tag in child_dict:
                    if not isinstance(child_dict[tag], list):
                        child_dict[tag] = [child_dict[tag]]
                    child_dict[tag].append(child_data)
                else:
                    child_dict[tag] = child_data
            result.update(child_dict)
        return result
