from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFileSystemModel, QTreeView

from apps.Abyssal.src.ui.styles import AbyssalTheme


class AbyssalFileTree(QTreeView):
    def __init__(self):
        super().__init__()
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.model.setNameFilterDisables(False)
        self.model.setNameFilters([
            "*.py", "*.js", "*.html", "*.css", "*.cpp", "*.c", "*.h",
            "*.sh", "*.json", "*.yaml", "*.md", "*.txt"
        ])
        self.setModel(self.model)
        self.setRootIndex(self.model.index(""))
        self.setHeaderHidden(True)
        for i in range(1, 4):
            self.hideColumn(i)
        self.setFont(QFont("JetBrains Mono", 9))
        self.setStyleSheet(f"""
            QTreeView {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: none;
                border-right: 1px solid {AbyssalTheme.BORDER};
            }}
            QTreeView::item {{
                padding: 4px;
                border: none;
            }}
            QTreeView::item:selected {{
                background-color: {AbyssalTheme.ACCENT};
                color: {AbyssalTheme.BG};
            }}
        """)
        self.expanded.connect(lambda: self.resizeColumnToContents(0))
        self.collapsed.connect(lambda: self.resizeColumnToContents(0))
        self.setAnimated(True)
        self.setIndentation(15)
        self.setUniformRowHeights(True)
