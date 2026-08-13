import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.Abyssal.src.ui.styles import AbyssalTheme


class SettingsDialog(QDialog):
    def __init__(self, config_dir: str, parent=None):
        super().__init__(parent)
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "abyssal_config.json")
        self._settings = {}
        self._theme = AbyssalTheme()
        
        self._setup_ui()
        self._setup_global_hotkeys()
        self._load_settings()
        self._apply_theme()

    def _setup_ui(self):
        self.setWindowTitle("Abyssal Configuration")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Header
        header = QLabel("Abyssal Editor Configuration")
        header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self._theme.TEXT};
            margin-bottom: 8px;
        """)
        layout.addWidget(header)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # General Settings Tab
        self._setup_general_tab()

        # Editor Settings Tab
        self._setup_editor_tab()

        # Appearance Tab
        self._setup_appearance_tab()

        # Keybindings Tab
        self._setup_keybindings_tab()

        # Advanced Tab
        self._setup_advanced_tab()

        # Footer
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 16, 0, 0)

        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedHeight(36)
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._theme.ACCENT};
                color: {self._theme.BG};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._theme.ACCENT_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {self._theme.ACCENT_DIM};
            }}
        """)
        footer_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setFixedHeight(36)
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._theme.PANEL};
                color: {self._theme.TEXT};
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self._theme.PANEL_HOVER};
            }}
        """)
        footer_layout.addWidget(self.reset_btn)

        layout.addWidget(footer_widget)

    def _create_labeled_field(self, label_text, parent_layout, tooltip=""):
        field_layout = QHBoxLayout()
        field_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setStyleSheet(f"""
            color: {self._theme.TEXT_DIM};
            font-size: 12px;
            min-width: 120px;
        """)
        label.setFixedWidth(120)
        field_layout.addWidget(label)

        return field_layout

    def _create_input_field(self, placeholder="", text_changed_callback=None):
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._theme.BG};
                color: {self._theme.TEXT};
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {self._theme.ACCENT};
            }}
        """)
        if text_changed_callback:
            input_field.textChanged.connect(text_changed_callback)
        return input_field

    def _create_check_box(self, checked=False, state_changed_callback=None):
        check_box = QCheckBox()
        check_box.setChecked(checked)
        check_box.setStyleSheet(f"""
            QCheckBox {{
                color: {self._theme.TEXT};
                font-size: 12px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
        """)
        if state_changed_callback:
            check_box.stateChanged.connect(state_changed_callback)
        return check_box

    def _create_combo_box(self, items, current_index=0, current_index_changed_callback=None):
        combo_box = QComboBox()
        for item in items:
            combo_box.addItem(item)
        combo_box.setCurrentIndex(current_index)
        combo_box.setStyleSheet(f"""
            QComboBox {{
                background-color: {self._theme.BG};
                color: {self._theme.TEXT};
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }}
            QComboBox:focus {{
                border-color: {self._theme.ACCENT};
            }}
        """)
        if current_index_changed_callback:
            combo_box.currentIndexChanged.connect(current_index_changed_callback)
        return combo_box

    def _create_spin_box(self, min_val, max_val, current_value, value_changed_callback=None, step=1):
        spin_box = QDoubleSpinBox() if isinstance(step, float) and not step.is_integer() else QSpinBox()
        spin_box.setMinimum(min_val)
        spin_box.setMaximum(max_val)
        spin_box.setValue(current_value)
        spin_box.setSingleStep(step)
        spin_box.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self._theme.BG};
                color: {self._theme.TEXT};
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }}
            QSpinBox:focus {{
                border-color: {self._theme.ACCENT};
            }}
        """)
        if value_changed_callback:
            spin_box.valueChanged.connect(value_changed_callback)
        return spin_box

    def _create_button(self, text, callback, style="default"):
        button = QPushButton(text)
        button.setFixedHeight(36)
        button.clicked.connect(callback)

        if style == "destructive":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._theme.CORAL};
                    color: {self._theme.BG};
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #FF8A65;
                }}
            """)
        elif style == "primary":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._theme.ACCENT};
                    color: {self._theme.BG};
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self._theme.ACCENT_LIGHT};
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._theme.PANEL};
                    color: {self._theme.TEXT};
                    border: 1px solid {self._theme.BORDER};
                    border-radius: 4px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {self._theme.PANEL_HOVER};
                }}
            """)
        return button

    def _create_text_area(self, placeholder, text_changed_callback=None):
        text_area = QTextEdit()
        text_area.setPlaceholderText(placeholder)
        text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._theme.BG};
                color: {self._theme.TEXT};
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border-color: {self._theme.ACCENT};
            }}
        """)
        if text_changed_callback:
            text_area.textChanged.connect(text_changed_callback)
        return text_area

    def _create_color_button(self, color, callback):
        button = QPushButton()
        button.setFixedSize(36, 36)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {self._theme.ACCENT};
            }}
        """)
        button.clicked.connect(callback)
        return button

    def _create_hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {self._theme.BORDER};")
        return line

    def _setup_general_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Application Settings
        app_group = QGroupBox("Application Settings")
        app_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        app_layout = QFormLayout(app_group)
        app_layout.setVerticalSpacing(8)

        self.app_name_input = self._create_input_field("Abyssal Editor")
        app_layout.addRow("Application Name:", self.app_name_input)

        self.version_input = self._create_input_field("2.0.0")
        app_layout.addRow("Version:", self.version_input)

        self.working_dir_input = self._create_input_field("~/projects")
        app_layout.addRow("Default Working Directory:", self.working_dir_input)

        layout.addWidget(app_group)

        # Startup Options
        startup_group = QGroupBox("Startup Options")
        startup_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        startup_layout = QFormLayout(startup_group)
        startup_layout.setVerticalSpacing(8)

        self.startup_open_last_file = self._create_check_box(False)
        startup_layout.addRow("Open Last File:", self.startup_open_last_file)

        self.startup_use_settings = self._create_check_box(True)
        startup_layout.addRow("Restore Settings:", self.startup_use_settings)

        self.confirm_on_exit = self._create_check_box(True)
        startup_layout.addRow("Confirm on Exit:", self.confirm_on_exit)

        layout.addWidget(startup_group)

        scroll.setWidget(widget)
        self.tab_widget.addTab(scroll, "General")

    def _setup_editor_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Font Settings
        font_group = QGroupBox("Font Settings")
        font_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        font_layout = QFormLayout(font_group)
        font_layout.setVerticalSpacing(8)

        self.font_family_input = self._create_input_field("JetBrains Mono")
        font_layout.addRow("Font Family:", self.font_family_input)

        self.font_size_input = self._create_spin_box(8, 32, 14)
        font_layout.addRow("Font Size:", self.font_size_input)

        self.line_height_input = self._create_spin_box(1, 10, 1, step=0.1)
        font_layout.addRow("Line Height:", self.line_height_input)

        self.tab_size_input = self._create_spin_box(1, 12, 4)
        font_layout.addRow("Tab Size:", self.tab_size_input)

        layout.addWidget(font_group)

        # Editor Behavior
        behavior_group = QGroupBox("Editor Behavior")
        behavior_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        behavior_layout = QFormLayout(behavior_group)
        behavior_layout.setVerticalSpacing(8)

        self.auto_indent_check = self._create_check_box(True)
        behavior_layout.addRow("Auto Indent:", self.auto_indent_check)

        self.word_wrap_check = self._create_check_box(False)
        behavior_layout.addRow("Word Wrap:", self.word_wrap_check)

        self.show_whitespace_check = self._create_check_box(False)
        behavior_layout.addRow("Show Whitespace:", self.show_whitespace_check)

        self.highlight_brackets_check = self._create_check_box(True)
        behavior_layout.addRow("Highlight Matching Brackets:", self.highlight_brackets_check)

        layout.addWidget(behavior_group)

        # Default Language
        lang_group = QGroupBox("Default Language")
        lang_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        lang_layout = QFormLayout(lang_group)
        lang_layout.setVerticalSpacing(8)

        self.default_language_combo = self._create_combo_box(
            ["python", "javascript", "typescript", "html", "css", "json", "markdown"], 0
        )
        lang_layout.addRow("Default Language:", self.default_language_combo)

        layout.addWidget(lang_group)

        scroll.setWidget(widget)
        self.tab_widget.addTab(scroll, "Editor")

    def _setup_appearance_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Color Scheme
        color_scheme_group = QGroupBox("Color Scheme")
        color_scheme_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        color_scheme_layout = QGridLayout(color_scheme_group)
        color_scheme_layout.setVerticalSpacing(8)

        # Theme preview
        self.theme_preview = QLabel("Theme Preview")
        self.theme_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {self._theme.BG};
                color: {self._theme.TEXT};
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                padding: 12px;
                font-size: 12px;
            }}
        """)
        color_scheme_layout.addWidget(self.theme_preview, 0, 0)

        # Theme selection
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet(f"color: {self._theme.TEXT_DIM}; font-size: 12px;")
        color_scheme_layout.addWidget(theme_label, 1, 0)

        self.theme_selector = self._create_combo_box(
            ["Abyssal Dark", "Abyssal Light", "Monokai", "Nord", "GitHub"], 0
        )
        color_scheme_layout.addWidget(self.theme_selector, 1, 1)

        layout.addWidget(color_scheme_group)

        # UI Elements
        ui_group = QGroupBox("UI Elements")
        ui_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        ui_layout = QFormLayout(ui_group)
        ui_layout.setVerticalSpacing(8)

        self.sidebar_width_input = self._create_spin_box(200, 400, 260)
        ui_layout.addRow("Sidebar Width:", self.sidebar_width_input)

        self.status_bar_check = self._create_check_box(True)
        ui_layout.addRow("Show Status Bar:", self.status_bar_check)

        self.minimap_check = self._create_check_box(False)
        ui_layout.addRow("Show Minimap:", self.minimap_check)

        self.animation_check = self._create_check_box(True)
        ui_layout.addRow("Enable Animations:", self.animation_check)

        layout.addWidget(ui_group)

        scroll.setWidget(widget)
        self.tab_widget.addTab(scroll, "Appearance")

    def _setup_keybindings_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Keybinding mode
        mode_group = QGroupBox("Keybinding Mode")
        mode_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        mode_layout = QFormLayout(mode_group)
        mode_layout.setVerticalSpacing(8)

        self.keybinding_mode_combo = self._create_combo_box(
            ["Standard", "Vim", "Emacs"], 0
        )
        mode_layout.addRow("Mode:", self.keybinding_mode_combo)

        # Custom keybindings
        custom_group = QGroupBox("Custom Keybindings")
        custom_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        custom_layout = QVBoxLayout(custom_group)
        custom_layout.setVerticalSpacing(8)

        self.custom_keybindings_text = self._create_text_area(
            "Enter custom keybindings in JSON format, e.g.:\n{\"Ctrl+Shift+F\": \"search.find\"}"
        )
        custom_layout.addWidget(self.custom_keybindings_text)

        help_label = QLabel("Note: Custom keybindings will be loaded and merged with default bindings.")
        help_label.setStyleSheet(f"""
            color: {self._theme.TEXT_MUTED};
            font-size: 10px;
            font-style: italic;
        """)
        custom_layout.addWidget(help_label)

        layout.addWidget(mode_group)
        layout.addWidget(custom_group)

        scroll.setWidget(widget)
        self.tab_widget.addTab(scroll, "Keybindings")

    def _setup_advanced_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Performance
        perf_group = QGroupBox("Performance")
        perf_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        perf_layout = QFormLayout(perf_group)
        perf_layout.setVerticalSpacing(8)

        self.max_undo_input = self._create_spin_box(100, 1000, 100)
        perf_layout.addRow("Max Undo Steps:", self.max_undo_input)

        self.max_recent_files_input = self._create_spin_box(10, 100, 20)
        perf_layout.addRow("Max Recent Files:", self.max_recent_files_input)

        self.auto_save_check = self._create_check_box(False)
        auto_save_layout = QHBoxLayout()
        auto_save_layout.addWidget(self.auto_save_check)
        auto_save_layout.addStretch()
        perf_layout.addRow("Auto Save:", auto_save_layout)

        self.auto_save_delay_input = self._create_spin_box(1, 60, 5)
        auto_save_layout2 = QHBoxLayout()
        auto_save_layout2.addWidget(self.auto_save_delay_input)
        auto_save_layout2.addWidget(QLabel(" seconds"))
        auto_save_layout2.addStretch()
        perf_layout.addRow("Auto Save Delay:", auto_save_layout2)

        layout.addWidget(perf_group)

        # Debug Options
        debug_group = QGroupBox("Debug Options")
        debug_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self._theme.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {self._theme.TEXT_DIM};
            }}
        """)
        debug_layout = QFormLayout(debug_group)
        debug_layout.setVerticalSpacing(8)

        self.dev_mode_check = self._create_check_box(False)
        debug_layout.addRow("Developer Mode:", self.dev_mode_check)

        self.log_level_combo = self._create_combo_box(
            ["Error", "Warning", "Info", "Debug"], 1
        )
        debug_layout.addRow("Log Level:", self.log_level_combo)

        self.performance_profiling_check = self._create_check_box(False)
        debug_layout.addRow("Performance Profiling:", self.performance_profiling_check)

        layout.addWidget(debug_group)

        scroll.setWidget(widget)
        self.tab_widget.addTab(scroll, "Advanced")

    def _setup_global_hotkeys(self):
        self.hotkeys = {
            Qt.Key_Escape: self._close_settings,
            Qt.Key_Return: self._apply_settings,
            Qt.Key_Space: self._toggle_theme,
        }

    def keyPressEvent(self, event):
        if event.key() in self.hotkeys:
            self.hotkeys[event.key()](event)
        else:
            super().keyPressEvent(event)

    def _close_settings(self, event=None):
        self.reject()

    def _apply_settings(self, event=None):
        self._save_settings()
        self.accept()

    def _toggle_theme(self, event=None):
        self._next_theme_index = (self.theme_selector.currentIndex() + 1) % self.theme_selector.count()
        self.theme_selector.setCurrentIndex(self._next_theme_index)
        self._apply_theme()

    def _load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file) as f:
                    settings = json.load(f)
                    self._apply_settings_to_ui(settings)
            except Exception as e:
                print(f"Error loading settings: {e}")
                self._set_default_settings()
        else:
            self._set_default_settings()

    def _apply_settings_to_ui(self, settings):
        # General tab
        self.app_name_input.setText(settings.get("app_name", "Abyssal Editor"))
        self.version_input.setText(settings.get("app_version", "2.0.0"))
        self.working_dir_input.setText(settings.get("working_dir", "~/projects"))

        self.startup_open_last_file.setChecked(settings.get("startup_open_last_file", False))
        self.startup_use_settings.setChecked(settings.get("startup_use_settings", True))
        self.confirm_on_exit.setChecked(settings.get("confirm_on_exit", True))

        # Editor tab
        self.font_family_input.setText(settings.get("font_family", "JetBrains Mono"))
        self.font_size_input.setValue(settings.get("font_size", 14))
        self.line_height_input.setValue(settings.get("line_height", 1))
        self.tab_size_input.setValue(settings.get("tab_size", 4))

        self.auto_indent_check.setChecked(settings.get("auto_indent", True))
        self.word_wrap_check.setChecked(settings.get("word_wrap", False))
        self.show_whitespace_check.setChecked(settings.get("show_whitespace", False))
        self.highlight_brackets_check.setChecked(settings.get("highlight_brackets", True))

        self.default_language_combo.setCurrentIndex(
            self.default_language_combo.findText(settings.get("default_language", "python"))
        )

        # Appearance tab
        theme_index = self.theme_selector.findText(settings.get("theme", "Abyssal Dark"))
        if theme_index >= 0:
            self.theme_selector.setCurrentIndex(theme_index)

        self.sidebar_width_input.setValue(settings.get("sidebar_width", 260))
        self.status_bar_check.setChecked(settings.get("status_bar_visible", True))
        self.minimap_check.setChecked(settings.get("minimap_visible", False))
        self.animation_check.setChecked(settings.get("animations_enabled", True))

        # Keybindings tab
        mode_index = self.keybinding_mode_combo.findText(settings.get("keybinding_mode", "Standard"))
        if mode_index >= 0:
            self.keybinding_mode_combo.setCurrentIndex(mode_index)

        self.custom_keybindings_text.setText(settings.get("custom_keybindings", ''))

        # Advanced tab
        self.max_undo_input.setValue(settings.get("max_undo", 100))
        self.max_recent_files_input.setValue(settings.get("max_recent_files", 20))
        self.auto_save_check.setChecked(settings.get("auto_save", False))
        self.auto_save_delay_input.setValue(settings.get("auto_save_delay", 5))

        self.dev_mode_check.setChecked(settings.get("dev_mode", False))
        log_level_index = self.log_level_combo.findText(settings.get("log_level", "Warning"))
        if log_level_index >= 0:
            self.log_level_combo.setCurrentIndex(log_level_index)
        self.performance_profiling_check.setChecked(settings.get("performance_profiling", False))

    def _set_default_settings(self):
        self.app_name_input.setText("Abyssal Editor")
        self.version_input.setText("2.0.0")
        self.working_dir_input.setText("~/projects")

        self.startup_open_last_file.setChecked(False)
        self.startup_use_settings.setChecked(True)
        self.confirm_on_exit.setChecked(True)

        self.font_family_input.setText("JetBrains Mono")
        self.font_size_input.setValue(14)
        self.line_height_input.setValue(1)
        self.tab_size_input.setValue(4)

        self.auto_indent_check.setChecked(True)
        self.word_wrap_check.setChecked(False)
        self.show_whitespace_check.setChecked(False)
        self.highlight_brackets_check.setChecked(True)

        self.default_language_combo.setCurrentIndex(0)

        self.theme_selector.setCurrentIndex(0)
        self.sidebar_width_input.setValue(260)
        self.status_bar_check.setChecked(True)
        self.minimap_check.setChecked(False)
        self.animation_check.setChecked(True)

        self.keybinding_mode_combo.setCurrentIndex(0)
        self.custom_keybindings_text.setText('')

        self.max_undo_input.setValue(100)
        self.max_recent_files_input.setValue(20)
        self.auto_save_check.setChecked(False)
        self.auto_save_delay_input.setValue(5)

        self.dev_mode_check.setChecked(False)
        self.log_level_combo.setCurrentIndex(1)
        self.performance_profiling_check.setChecked(False)

    def _collect_settings_from_ui(self):
        settings = {}

        # General tab
        settings["app_name"] = self.app_name_input.text()
        settings["app_version"] = self.version_input.text()
        settings["working_dir"] = self.working_dir_input.text()

        settings["startup_open_last_file"] = self.startup_open_last_file.isChecked()
        settings["startup_use_settings"] = self.startup_use_settings.isChecked()
        settings["confirm_on_exit"] = self.confirm_on_exit.isChecked()

        # Editor tab
        settings["font_family"] = self.font_family_input.text()
        settings["font_size"] = self.font_size_input.value()
        settings["line_height"] = self.line_height_input.value()
        settings["tab_size"] = self.tab_size_input.value()

        settings["auto_indent"] = self.auto_indent_check.isChecked()
        settings["word_wrap"] = self.word_wrap_check.isChecked()
        settings["show_whitespace"] = self.show_whitespace_check.isChecked()
        settings["highlight_brackets"] = self.highlight_brackets_check.isChecked()

        settings["default_language"] = self.default_language_combo.currentText()

        # Appearance tab
        settings["theme"] = self.theme_selector.currentText()
        settings["sidebar_width"] = self.sidebar_width_input.value()
        settings["status_bar_visible"] = self.status_bar_check.isChecked()
        settings["minimap_visible"] = self.minimap_check.isChecked()
        settings["animations_enabled"] = self.animation_check.isChecked()

        # Keybindings tab
        settings["keybinding_mode"] = self.keybinding_mode_combo.currentText()
        settings["custom_keybindings"] = self.custom_keybindings_text.toPlainText()

        # Advanced tab
        settings["max_undo"] = self.max_undo_input.value()
        settings["max_recent_files"] = self.max_recent_files_input.value()
        settings["auto_save"] = self.auto_save_check.isChecked()
        settings["auto_save_delay"] = self.auto_save_delay_input.value()

        settings["dev_mode"] = self.dev_mode_check.isChecked()
        settings["log_level"] = self.log_level_combo.currentText()
        settings["performance_profiling"] = self.performance_profiling_check.isChecked()

        return settings

    def _save_settings(self):
        settings = self._collect_settings_from_ui()

        try:
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)

            self._apply_theme()

            QMessageBox.information(self, "Settings", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e!s}")

    def _apply_theme(self):
        from apps.Abyssal.src.ui.styles import AbyssalTheme

        theme_map = {
            "Abyssal Dark": AbyssalTheme,
            "Abyssal Light": AbyssalTheme,
            "Monokai": AbyssalTheme,
            "Nord": AbyssalTheme,
            "GitHub": AbyssalTheme,
        }

        current_theme = theme_map.get(self.theme_selector.currentText(), AbyssalTheme)

        if current_theme == AbyssalTheme:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {current_theme.BG};
                    color: {current_theme.TEXT};
                }}
            """)
            self.theme_preview.setStyleSheet(f"""
                QLabel {{
                    background-color: {current_theme.BG};
                    color: {current_theme.TEXT};
                }}
            """)

    def _reset_to_defaults(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to their defaults?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._set_default_settings()
            QMessageBox.information(self, "Settings", "Settings have been reset to defaults.")


SettingsPanel = SettingsDialog
