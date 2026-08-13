"""
Kraken AI — main desktop window.

Composes the chat panel and workforce tree, and runs the engine on a
background thread. Engine events are marshalled to the Qt thread via a
polled queue so no cross-thread Qt calls are ever made.
"""

import os
import queue
import threading

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from apps.kraken.engine.agent_store import AgentStore, SpecError
from apps.kraken.engine.config import DEFAULT_PROVIDERS, KrakenConfig
from apps.kraken.engine.discovery import find_local_models
from apps.kraken.engine.keys import get_key
from apps.kraken.engine.logger import engine_logger
from apps.kraken.engine.memory import MemoryStore
from apps.kraken.engine.providers import ChatClient, ProviderError
from apps.kraken.engine.spec import AgentSpec
from apps.kraken.engine.tools import PermissionGate
from apps.kraken.ui.chat_panel import ChatPanel
from apps.kraken.ui.workforce_view import WorkforceTree

log = engine_logger()

try:
    from core.theme import COLORS, FONTS
except ImportError:
    # Standalone fallback: same Nautilus palette, no core.theme dependency.
    COLORS = {
        "abyss_navy": "#081626",
        "slate_navy": "#0E2238",
        "deep_navy": "#050D14",
        "void_black": "#02060A",
        "seafoam": "#00F2C2",
        "seafoam_deep": "#004D40",
        "coral": "#FF7F50",
        "amber": "#FFA502",
        "emerald": "#00C853",
        "hd_white": "#EEF4F8",
        "text_secondary": "#8BA4B8",
        "text_muted": "#506070",
        "border": "#152D44",
        "surface_selected": "#1A3352",
    }
    FONTS = {
        "mono": "JetBrains Mono",
        "ui": "Segoe UI",
        "size_xs": 10,
        "size_sm": 11,
        "size_md": 12,
        "size_lg": 13,
    }


class EngineWorker:
    """Runs single agents or a workforce off the Qt thread."""

    def __init__(self, cfg: KrakenConfig, store=None):
        self.cfg = cfg
        self.store = store
        self.events: queue.Queue = queue.Queue()
        self._current = None
        self.running = False

    # ── Event plumbing ─────────────────────────────────────────
    def _put(self, ev):
        self.events.put(
            {
                "kind": ev.kind,
                "message": ev.message,
                "data": ev.data,
            }
        )

    # ── Lifecycle ──────────────────────────────────────────────
    def build_client(self) -> ChatClient:
        return ChatClient(
            provider=self.cfg.provider,
            base_url=self.cfg.base_url,
            model=self.cfg.model,
            temperature=self.cfg.get("temperature", 0.2),
            max_tokens=self.cfg.get("max_tokens", 4096),
            num_ctx=self.cfg.get("num_ctx", 8192),
            api_key=self.cfg.get("api_key") or get_key(self.cfg.home_dir, self.cfg.provider),
            timeout=self.cfg.get("timeout", 300),
        )

    def gate(self) -> PermissionGate:
        return PermissionGate(auto_approve=bool(self.cfg.get("auto_approve", False)))

    def run_agent(self, task: str, spec: AgentSpec):
        def _target():
            self.running = True
            self._put_kind("status", f"[{spec.name}] starting single-agent run")
            try:
                client = self.build_client()
                memory = MemoryStore(self.cfg.memory_path, enabled=bool(self.cfg.get("memory_enabled", True)))
                from apps.kraken.engine.agent import Agent

                agent = Agent(
                    spec=spec,
                    client=client,
                    workspace=self.cfg.workspace,
                    gate=self.gate(),
                    memory=memory,
                    callbacks=[self._put],
                    max_rounds=int(self.cfg.get("max_agent_rounds", 12)),
                )
                self._current = agent
                agent.run(task)
            except ProviderError as e:
                self._put_kind("error", str(e))
            except Exception as e:  # defensive
                log.error(f"agent thread crashed: {e}", exc_info=True)
                self._put_kind("error", f"engine error: {e}")
            finally:
                self.running = False
                self._put_kind("done", "run finished")

        threading.Thread(target=_target, daemon=True, name="kraken-single").start()

    def run_workforce(self, task: str, spec: AgentSpec):
        def _target():
            self.running = True
            self._put_kind("status", f"[{spec.name}] spawning workforce")
            try:
                client = self.build_client()
                from apps.kraken.engine.orchestrator import Orchestrator

                orch = Orchestrator(
                    client=client,
                    workspace=self.cfg.workspace,
                    gate=self.gate(),
                    spec=spec,
                    max_parallel=int(self.cfg.get("max_parallel_workers", 3)),
                    callbacks=[self._put],
                    store=self.store,
                )
                self._current = orch
                orch.run(task)
            except ProviderError as e:
                self._put_kind("error", str(e))
            except Exception as e:  # defensive
                log.error(f"orchestrator thread crashed: {e}", exc_info=True)
                self._put_kind("error", f"engine error: {e}")
            finally:
                self.running = False
                self._put_kind("done", "workforce finished")

        threading.Thread(target=_target, daemon=True, name="kraken-orchestrator").start()

    def stop(self):
        if self._current is not None:
            self._current.stop()

    def _put_kind(self, kind: str, message: str, data: dict | None = None):
        self.events.put({"kind": kind, "message": message, "data": data or {}})


class KrakenWindow(QMainWindow):
    """Kraken AI desktop app — chat + workforce control panel."""

    def __init__(self, cfg: KrakenConfig):
        super().__init__()
        self.cfg = cfg
        self.agent_store = AgentStore(cfg.agents_dir)
        self.worker = EngineWorker(cfg, store=self.agent_store)

        self.colors = COLORS
        self.fonts = FONTS

        self.setWindowTitle("Kraken AI")
        self.resize(1180, 760)
        self._build_ui()
        self._bind_shortcuts()
        self._load_persisted_spec()

        self._poll = QTimer(self)
        self._poll.timeout.connect(self._drain_events)
        self._poll.start(120)
        self._update_status_bar()
        self.chat.status(f"provider: {self.cfg.provider} · model: {self.cfg.model}")
        self.chat.status(f"workspace: {self.cfg.workspace}")

    # ── UI construction ────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet(f"background: {self.colors['abyss_navy']};")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.chat = ChatPanel(self.colors, self.fonts)

        outer.addWidget(self._build_top_bar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {self.colors['border']}; }}")

        splitter.addWidget(self.chat)

        right = QWidget()
        right.setStyleSheet(f"background: {self.colors['slate_navy']};")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        header = QLabel("  WORKFORCE / AGENTS")
        header.setStyleSheet(
            f"color: {self.colors['seafoam']}; font-family: '{self.fonts['mono']}'; "
            f"font-size: {self.fonts['size_xs']}px; padding: 8px 4px; "
            f"background: {self.colors['void_black']}; letter-spacing: 1px;"
        )
        right_lay.addWidget(header)

        self.tree = WorkforceTree(self.colors, self.fonts)
        right_lay.addWidget(self.tree, 1)

        right.setMinimumWidth(360)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([720, 440])
        outer.addWidget(splitter, 1)

        self.chat.submitted.connect(self._on_submit)
        self.chat.focus_input()
        self.statusBar().setStyleSheet(
            f"color: {self.colors['text_secondary']}; background: {self.colors['void_black']}; "
            f"font-family: '{self.fonts['mono']}'; font-size: {self.fonts['size_xs']}px;"
        )

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(f"background: {self.colors['void_black']}; border-bottom: 1px solid {self.colors['border']};")
        bar.setFixedHeight(54)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 0, 12, 0)

        brand = QLabel("KRAKEN AI")
        brand.setStyleSheet(
            f"color: {self.colors['seafoam']}; font-family: '{self.fonts['mono']}'; "
            f"font-size: {self.fonts['size_lg']}px; font-weight: bold; letter-spacing: 2px; background: transparent;"
        )
        lay.addWidget(brand)
        lay.addSpacing(16)

        self._model_edit = QLineEdit(self.cfg.model)
        self._model_edit.setFixedWidth(220)
        self._model_edit.setToolTip("model name")
        self._model_edit.setStyleSheet(
            f"QLineEdit {{ background: {self.colors['deep_navy']}; color: {self.colors['seafoam']}; "
            f"border: 1px solid {self.colors['border']}; padding: 4px 8px; font-family: '{self.fonts['mono']}'; "
            f"font-size: {self.fonts['size_sm']}px; }}"
        )
        self._model_edit.editingFinished.connect(self._on_model_changed)
        lay.addWidget(self._model_edit)

        self._provider_edit = QLineEdit(self.cfg.provider)
        self._provider_edit.setFixedWidth(140)
        self._provider_edit.setToolTip("provider: ollama | lmstudio | vllm | llamacpp | custom")
        self._provider_edit.setStyleSheet(
            f"QLineEdit {{ background: {self.colors['deep_navy']}; color: {self.colors['amber']}; "
            f"border: 1px solid {self.colors['border']}; padding: 4px 8px; font-family: '{self.fonts['mono']}'; "
            f"font-size: {self.fonts['size_sm']}px; }}"
        )
        self._provider_edit.editingFinished.connect(self._on_provider_changed)
        lay.addWidget(self._provider_edit)

        self._models_combo = QComboBox()
        self._models_combo.setMinimumWidth(190)
        self._models_combo.setToolTip("downloaded local models (auto-detected)")
        self._models_combo.setStyleSheet(
            f"QComboBox {{ background: {self.colors['deep_navy']}; color: {self.colors['hd_white']}; "
            f"border: 1px solid {self.colors['border']}; padding: 4px 8px; font-family: '{self.fonts['mono']}'; "
            f"font-size: {self.fonts['size_sm']}px; }}"
            f"QComboBox QAbstractItemView {{ background: {self.colors['slate_navy']}; "
            f"color: {self.colors['hd_white']}; selection-background-color: {self.colors['surface_selected']}; }}"
        )
        self._models_combo.activated.connect(self._on_local_model_picked)
        self._refresh_models()
        lay.addWidget(self._models_combo)

        self._agent_mode = QCheckBox("AGENT MODE")
        self._agent_mode.setChecked(bool(self.cfg.get("agent_mode", False)))
        self._agent_mode.setStyleSheet(
            f"QCheckBox {{ color: {self.colors['seafoam']}; font-family: '{self.fonts['mono']}'; "
            f"font-size: {self.fonts['size_sm']}px; }}"
        )
        self._agent_mode.toggled.connect(self._on_agent_mode_toggled)
        lay.addWidget(self._agent_mode)
        lay.addStretch(1)

        self._stop_btn = self._button("STOP", self.colors["coral"])
        self._stop_btn.clicked.connect(self.worker.stop)
        self._stop_btn.setEnabled(False)
        lay.addWidget(self._stop_btn)

        lay.addStretch(1)

        self._agent_combo = QComboBox()
        self._agent_combo.setMinimumWidth(180)
        self._agent_combo.setToolTip("custom agent from the library (Kraken = built-in)")
        self._agent_combo.setStyleSheet(
            f"QComboBox {{ background: {self.colors['deep_navy']}; color: {self.colors['emerald']}; "
            f"border: 1px solid {self.colors['border']}; padding: 4px 8px; font-family: '{self.fonts['mono']}'; "
            f"font-size: {self.fonts['size_sm']}px; }}"
            f"QComboBox QAbstractItemView {{ background: {self.colors['slate_navy']}; "
            f"color: {self.colors['hd_white']}; selection-background-color: {self.colors['surface_selected']}; }}"
        )
        self._agent_combo.currentIndexChanged.connect(self._on_agent_selected)
        lay.addWidget(self._agent_combo)

        self._agent_new_btn = self._button("NEW", self.colors["seafoam"])
        self._agent_new_btn.clicked.connect(self._new_agent_dialog)
        lay.addWidget(self._agent_new_btn)

        self._agent_manage_btn = self._button("MANAGE", self.colors["amber"])
        self._agent_manage_btn.clicked.connect(self._manage_agents_dialog)
        lay.addWidget(self._agent_manage_btn)

        self._clear_btn = self._button("CLEAR", self.colors["text_secondary"])
        self._clear_btn.clicked.connect(self.chat.clear_log)
        lay.addWidget(self._clear_btn)

        self._spec_btn = self._button("LOAD SPEC", self.colors["amber"])
        self._spec_btn.clicked.connect(self._load_spec_dialog)
        lay.addWidget(self._spec_btn)

        self._refresh_agents()

        return bar

    def _button(self, text: str, accent: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: {self.colors['slate_navy']}; color: {accent}; "
            f"border: 1px solid {accent}; padding: 5px 12px; font-family: '{self.fonts['mono']}'; "
            f"font-size: {self.fonts['size_sm']}px; }}"
            f"QPushButton:hover {{ background: {self.colors['seafoam_deep']}; }}"
            f"QPushButton:disabled {{ color: {self.colors['text_muted']}; border-color: {self.colors['border']}; }}"
        )
        return btn

    def _bind_shortcuts(self):
        from PySide6.QtGui import QKeySequence, QShortcut

        QShortcut(QKeySequence("Ctrl+L"), self, self.chat.clear_log)
        QShortcut(QKeySequence("Ctrl+R"), self, self._on_submit_again)

    def _on_submit_again(self):
        self.chat.focus_input()

    # ── Behavior ───────────────────────────────────────────────
    def _on_submit(self, task: str):
        if self.worker.running:
            self.chat.error("engine busy — stop the current run first")
            return
        self.chat.user(task)
        spec = self._current_spec()
        if self._agent_mode.isChecked():
            self.chat.status("agent mode: orchestrating workforce for task…")
            self.worker.run_workforce(task, spec)
        else:
            self.worker.run_agent(task, spec)
        self._stop_btn.setEnabled(True)

    def _on_model_changed(self):
        self.cfg.set("model", self._model_edit.text().strip() or self.cfg.model)
        self._update_status_bar()

    def _on_provider_changed(self):
        provider = self._provider_edit.text().strip().lower()
        meta = DEFAULT_PROVIDERS.get(provider)
        if meta:
            self.cfg.set("provider", provider)
            self.cfg.set("base_url", meta["base_url"])
            self.chat.status(f"provider switched to {provider} → {meta['base_url']}")
        else:
            self.cfg.set("provider", provider)
            self.chat.status(f"provider set to custom: {provider} (set base URL via config)")
        self._update_status_bar()

    def _refresh_models(self):
        self._models_combo.clear()
        self._models_combo.addItem("… local models", None)
        for m in find_local_models():
            label = f"[{m['provider']}] {m['name']}"
            self._models_combo.addItem(label, m["name"])

    def _on_local_model_picked(self, index: int):
        name = self._models_combo.itemData(index)
        if not name:
            return
        self.cfg.set("model", name)
        self._model_edit.setText(name)
        self.chat.status(f"model set to {name}")

    def _on_agent_mode_toggled(self, checked: bool):
        self.cfg.set("agent_mode", checked)
        self.chat.status(f"agent mode {'ON — workforce' if checked else 'OFF — single agent'}")

    def _load_persisted_spec(self):
        path = self.cfg.get("active_spec")
        if path and os.path.exists(path):
            self._spec: AgentSpec | None = AgentSpec.from_file(path)
            self.chat.status(f"loaded spec: {self._spec.name}")
        else:
            self._spec = None

    def _current_spec(self) -> AgentSpec:
        if self._spec is not None:
            return self._spec
        return AgentSpec(
            name="Kraken",
            model=self.cfg.model,
            tools=self.cfg.get("tools") or ["file_read", "file_write", "terminal_exec"],
        )

    def _load_spec_dialog(self):
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "Load Agent Spec", self.cfg.workspace, "Markdown (*.md)")
        if not path:
            return
        try:
            self._spec = AgentSpec.from_file(path)
            self.cfg.set("active_spec", os.path.abspath(path))
            self.chat.status(f"spec loaded: {self._spec.name} (model {self._spec.model})")
            self._model_edit.setText(self._spec.model)
        except (OSError, ValueError) as e:
            self.chat.error(f"failed to load spec: {e}")

    # ── Agent library (desktop manager) ────────────────────────
    def _refresh_agents(self):
        selected = self._agent_combo.currentData() if hasattr(self, "_agent_combo") else None
        self._agent_combo.blockSignals(True)
        self._agent_combo.clear()
        self._agent_combo.addItem("Kraken (built-in)", None)
        for row in self.agent_store.list_agents():
            self._agent_combo.addItem(row["name"], row["name"])
        if selected is not None:
            idx = self._agent_combo.findData(selected)
            if idx >= 0:
                self._agent_combo.setCurrentIndex(idx)
        self._agent_combo.blockSignals(False)

    def _on_agent_selected(self, index: int):
        name = self._agent_combo.itemData(index)
        if name is None:
            return
        try:
            spec = self.agent_store.get_or_raise(name)
        except SpecError as e:
            self.chat.error(str(e))
            return
        self._spec = spec
        self.cfg.set("active_spec", spec.source_path)
        roles = f" · roles: {', '.join(spec.workforce_roles)}" if spec.workforce_roles else ""
        self.chat.status(f"agent loaded: {spec.name} (model {spec.model}){roles}")
        self._model_edit.setText(spec.model)

    def _new_agent_dialog(self):
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "New Agent", "name (e.g. ReviewCritic):")
        if not ok or not name.strip():
            return
        model, ok = QInputDialog.getText(self, "New Agent", "model:", text=self.cfg.model)
        if not ok:
            return
        try:
            spec = self.agent_store.create(
                name.strip(), model=model.strip() or None, role="",
            )
        except SpecError as e:
            self.chat.error(str(e))
            return
        self._refresh_agents()
        idx = self._agent_combo.findData(spec.name)
        if idx >= 0:
            self._agent_combo.setCurrentIndex(idx)
        self.chat.status(f"agent created: {spec.name} at {spec.source_path}")

    def _manage_agents_dialog(self):
        from PySide6.QtWidgets import (
            QAbstractItemView,
            QDialog,
            QHBoxLayout,
            QListWidget,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Agent Library")
        dialog.resize(460, 380)
        dialog.setStyleSheet(f"background: {self.colors['slate_navy']}; color: {self.colors['hd_white']};")

        layout = QVBoxLayout(dialog)
        list_widget = QListWidget(dialog)
        list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        list_widget.setStyleSheet(
            f"QListWidget {{ background: {self.colors['deep_navy']}; border: 1px solid {self.colors['border']}; "
            f"font-family: '{self.fonts['mono']}'; font-size: {self.fonts['size_sm']}px; }}"
            f"QListWidget::item:selected {{ background: {self.colors['surface_selected']}; }}"
        )
        for row in self.agent_store.list_agents():
            list_widget.addItem(f"{row['name']}  ({row['model']})  — {row['description'][:48]}")
        layout.addWidget(list_widget, 1)

        buttons = QHBoxLayout()
        actions = {
            "Load": "load",
            "Edit File": "edit",
            "Delete": "delete",
            "Refresh": "refresh",
        }

        def _act(action: str):
            if action == "refresh":
                self._refresh_agents()
                self.chat.status("agent library refreshed")
                dialog.close()
                return
            item = list_widget.currentItem()
            if item is None:
                return
            name = item.text().split("  ")[0]
            if action == "load":
                self._agent_combo.setCurrentIndex(self._agent_combo.findData(name))
                dialog.close()
            elif action == "edit":
                dialog.close()
                spec = self.agent_store.get_or_raise(name)
                self._open_agent_file(spec.source_path)
            elif action == "delete":
                if QMessageBox.question(
                    dialog, "Delete Agent", f"Remove agent {name} from the library?", "Yes", "No"
                ) == "Yes":
                    self.agent_store.remove(name)
                    if getattr(self, "_spec", None) and self._spec.name == name:
                        self._spec = None
                    self._refresh_agents()
                    self.chat.status(f"agent removed: {name}")

        for label, action in actions.items():
            btn = QPushButton(label, dialog)
            btn.setStyleSheet(
                f"QPushButton {{ background: {self.colors['slate_navy']}; color: {self.colors['seafoam']}; "
                f"border: 1px solid {self.colors['border']}; padding: 5px 12px; "
                f"font-family: '{self.fonts['mono']}'; }}"
            )
            btn.clicked.connect(lambda _=False, a=action: _act(a))
            buttons.addWidget(btn)

        layout.addLayout(buttons)
        dialog.exec()

    def _open_agent_file(self, path: str):
        import subprocess
        import sys

        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
        try:
            if editor:
                subprocess.Popen([editor, path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            elif os.name == "nt":
                os.startfile(path)  # noqa: S606
            else:
                subprocess.Popen(["xdg-open", path])
        except OSError as e:
            self.chat.error(f"could not open {path}: {e}")

    def _update_status_bar(self):
        status = (
            f"provider {self.cfg.provider} · model {self.cfg.model} · "
            f"auto-approve {'ON' if self.cfg.get('auto_approve') else 'OFF'} · "
            f"memory {'ON' if self.cfg.get('memory_enabled') else 'OFF'} · workspace {self.cfg.workspace}"
        )
        self.statusBar().showMessage(status)

    # ── Event drain (Qt thread) ────────────────────────────────
    def _drain_events(self):
        try:
            while True:
                ev = self.worker.events.get_nowait()
                self._handle_event(ev)
        except queue.Empty:
            pass

    def _handle_event(self, ev: dict):
        kind = ev["kind"]
        message = ev["message"]
        data = ev.get("data") or {}
        agent_id = data.get("agent_id") or ""

        if kind == "status":
            self.chat.stream_end()
            self.chat.status(message)
        elif kind == "text":
            if message.strip():
                self.chat.stream_begin()
                self.chat.assistant(message)
        elif kind == "tool":
            self.chat.stream_end()
            self.chat.tool(message)
            if agent_id:
                self.tree.add_event(agent_id, message, "tool")
        elif kind == "retry":
            self.chat.stream_end()
            self.chat.tool(message)
            if agent_id:
                self.tree.add_event(agent_id, message, "retry")
        elif kind == "memory":
            self.chat.stream_end()
            self.chat.memory(message)
            if agent_id:
                self.tree.add_event(agent_id, message, "memory")
        elif kind == "error":
            self.chat.stream_end()
            self.chat.error(message)
            if agent_id:
                self.tree.add_event(agent_id, message, "error")
            self._stop_btn.setEnabled(False)
        elif kind == "log":
            self.chat.stream_end()
            self.chat.tool(message)
        elif kind == "token":
            if agent_id:
                self.tree.add_tokens(agent_id, int(data.get("tokens", 0)))
        elif kind == "plan":
            self.chat.stream_end()
            self.tree.begin_workforce(data.get("plan") or [])
        elif kind == "agent_start":
            self.tree.add_agent(message, agent_id)
        elif kind == "agent_done":
            if agent_id:
                self.tree.update_agent_status(agent_id, data.get("status", "done"))
        elif kind == "done":
            self.chat.stream_end()
            self._stop_btn.setEnabled(False)
            self.tree.set_orchestrator_state("idle")
        self._update_status_bar()
