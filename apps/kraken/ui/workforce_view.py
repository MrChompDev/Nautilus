"""
Kraken AI — workforce tree view.

Real-time view of active sub-agents in Agent Mode: per-agent status, token
throughput, and a live event/log trail. Pure view; the main window feeds it.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem

try:
    from core.theme import COLORS, FONTS, glass_bg, glass_bg_dark, glass_edge, glass_sheen
except ImportError:
    COLORS = {}
    FONTS = {}
    def hex_to_rgba(h, a=255):
        v = h.lstrip("#")
        return f"rgba({int(v[0:2],16)},{int(v[2:4],16)},{int(v[4:6],16)},{a})"
    def glass_bg(a=180): return hex_to_rgba(COLORS.get("slate_navy", "#0E2238"), a)
    def glass_bg_dark(a=140): return hex_to_rgba(COLORS.get("deep_navy", "#050D14"), a)
    def glass_edge(a=48): return hex_to_rgba(COLORS.get("seafoam", "#00F2C2"), a)
    def glass_sheen(): return "rgba(238, 244, 248, 26)"

STATUS_COLORS = {
    "running": "#00F2C2",
    "done": "#00C853",
    "failed": "#FF7F50",
    "error": "#FF7F50",
    "pending": "#8BA4B8",
    "stopping": "#FFA502",
    "stopped": "#FFA502",
    "idle": "#506070",
}


class WorkforceTree(QTreeWidget):
    """Tree of agents + orchestrator with live activity."""

    def __init__(self, colors: dict, fonts: dict, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._fonts = fonts
        self._agents: dict[str, QTreeWidgetItem] = {}
        self._event_count: dict[str, int] = {}
        self._token_count: dict[str, int] = {}
        self._root = None
        self._build_ui()

    def _build_ui(self):
        self.setColumnCount(2)
        self.setHeaderLabels(["Agent / Event", "State"])
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.setIndentation(14)
        self.setRootIsDecorated(True)
        self.setStyleSheet(
            f"""
            QTreeWidget {{
                background: {glass_bg(130)};
                color: {self._colors['hd_white']};
                border: 1px solid {glass_edge()};
                border-radius: 12px;
                font-family: "{self._fonts['mono']}";
                font-size: {self._fonts['size_sm']}px;
            }}
            QTreeWidget::item {{ padding: 2px 4px; border-radius: 6px; }}
            QTreeWidget::item:selected {{ background: {self._colors['surface_selected']}; border-radius: 6px; }}
            """
        )

    # ── Tree construction ──────────────────────────────────────
    def begin_workforce(self, plan: list[str]):
        self.clear()
        self._agents.clear()
        self._event_count.clear()
        self._token_count.clear()
        self._root = QTreeWidgetItem(["ORCHESTRATOR", "running"])
        self._root.setForeground(0, QColor(self._colors["seafoam"]))
        self._root.setForeground(1, QColor(self._colors["seafoam"]))
        self.addTopLevelItem(self._root)
        for i, title in enumerate(plan, 1):
            node = QTreeWidgetItem([f"  Worker {i}: {title}", "pending"])
            node.setForeground(1, QColor(STATUS_COLORS["pending"]))
            node.setData(0, Qt.UserRole, {"type": "plan", "title": title})
            self._root.addChild(node)
        self.expandAll()

    def add_agent(self, title: str, agent_id: str):
        node = QTreeWidgetItem([f"{title}  [{agent_id}]", "running"])
        node.setForeground(1, QColor(STATUS_COLORS["running"]))
        self._agents[agent_id] = node
        if self._root:
            self._root.addChild(node)
        else:
            self.addTopLevelItem(node)
        self._token_count[agent_id] = 0
        self.expandAll()

    def update_agent_status(self, agent_id: str, status: str):
        node = self._agents.get(agent_id)
        if node is None:
            return
        color = STATUS_COLORS.get(status, self._colors["text_secondary"])
        node.setText(1, status)
        node.setForeground(1, QColor(color))
        if status == "done":
            node.setForeground(0, QColor(self._colors["emerald"]))
        elif status in ("failed", "error"):
            node.setForeground(0, QColor(self._colors["coral"]))

    def add_event(self, agent_id: str, message: str, kind: str = "log"):
        node = self._agents.get(agent_id)
        if node is None:
            return
        color = {
            "tool": self._colors["amber"],
            "retry": self._colors["amber"],
            "memory": self._colors["emerald"],
            "error": self._colors["coral"],
        }.get(kind, self._colors["text_muted"])
        self._event_count[agent_id] = self._event_count.get(agent_id, 0) + 1
        child = QTreeWidgetItem([f"    {message[:110]}", ""])
        child.setForeground(0, QColor(color))
        node.addChild(child)
        node.setExpanded(True)
        while node.childCount() > 60:
            node.removeChild(node.child(0))
        self.scrollToItem(child)

    def add_tokens(self, agent_id: str, tokens: int):
        self._token_count[agent_id] = self._token_count.get(agent_id, 0) + tokens
        node = self._agents.get(agent_id)
        if node is not None:
            node.setText(1, f"running · {self._token_count[agent_id]} tok")

    def set_orchestrator_state(self, status: str, tokens: int = 0):
        if self._root:
            color = STATUS_COLORS.get(status, self._colors["text_secondary"])
            self._root.setText(1, f"{status}{(' · ' + str(tokens) + ' tok') if tokens else ''}")
            self._root.setForeground(1, QColor(color))

    def reset(self):
        self.clear()
        self._agents.clear()
        self._event_count.clear()
        self._token_count.clear()
        self._root = None
