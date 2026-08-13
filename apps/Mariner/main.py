#!/usr/bin/env python3
"""
Mariner — Nautilus Scientific Calculator
Keyboard-first RPN-free calculator: expression evaluator, history tape,
unit-style navicational helpers (knots, nautical miles, bearings), and
deep history persistence.
"""

import json
import math
import os
import re
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

try:
    from core.logger import get_logger
    from core.theme import (
        COLORS,
        FONTS,
        SPACING,
        create_nautilus_palette,
        get_global_stylesheet,
    )
except ImportError:
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
        "seafoam_deep": "#004D40", "coral": "#FF7F50", "amber": "#FFA502",
        "emerald": "#00C853", "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8",
        "text_muted": "#506070", "border": "#152D44", "surface_hover": "#132A40",
        "surface_selected": "#1A3352", "scrollbar_bg": "#050D14", "scrollbar_handle": "#1A3352",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11, "size_md": 12, "size_lg": 13, "size_xl": 14}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "xxl": 24}

    def get_global_stylesheet(): return ""
    def create_nautilus_palette(): return QPalette()

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")


class ExpressionEvaluator:
    """Safe math expression evaluator with a whitelisted function set."""

    SAFE_FUNCS = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "asin": math.asin, "acos": math.acos, "atan": math.atan, "atan2": math.atan2,
        "sqrt": math.sqrt, "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
        "abs": abs, "floor": math.floor, "ceil": math.ceil, "round": round,
        "log": math.log10, "log10": math.log10, "log2": math.log2, "ln": math.log,
        "exp": math.exp, "pow": math.pow, "hypot": math.hypot,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "degrees": math.degrees, "radians": math.radians,
        "gcd": math.gcd, "fact": math.factorial,
    }

    SAFE_CONSTS = {
        "pi": math.pi, "e": math.e, "tau": math.tau, "phi": (1 + math.sqrt(5)) / 2,
    }

    @classmethod
    def _factorial(cls, value: float) -> float:
        if math.isnan(value) or value < 0:
            raise ValueError("factorial: invalid argument")
        if abs(value - round(value)) < 1e-9:
            return float(math.factorial(int(round(value))))
        return math.gamma(value + 1)

    TOKEN = re.compile(r"""
        \s*(?:
            (?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?) |
            (?P<ident>[a-zA-Z_][a-zA-Z0-9_]*) |
            (?P<op>[+\-*/%^!(),]) |
            (?P<err>.)
        )""", re.VERBOSE)

    @classmethod
    def evaluate(cls, expression: str) -> float:
        expr = expression.strip()
        if not expr:
            raise ValueError("Empty expression")

        tokens = []
        for m in cls.TOKEN.finditer(expr):
            if m.group("num"):
                tokens.append(("num", float(m.group("num"))))
            elif m.group("ident"):
                tokens.append(("ident", m.group("ident")))
            elif m.group("op"):
                tokens.append(("op", m.group("op")))
            elif m.group("err"):
                raise ValueError(f"Unexpected character: {m.group('err')}")
        if not tokens:
            raise ValueError("Empty expression")

        pos = [0]

        def peek():
            return tokens[pos[0]] if pos[0] < len(tokens) else None

        def advance():
            t = tokens[pos[0]]
            pos[0] += 1
            return t

        def parse_expr():
            value = parse_term()
            while True:
                t = peek()
                if t and t[0] == "op" and t[1] in ("+", "-"):
                    advance()
                    rhs = parse_term()
                    value = value + rhs if t[1] == "+" else value - rhs
                else:
                    return value

        def parse_term():
            value = parse_factor()
            while True:
                t = peek()
                if t and t[0] == "op" and t[1] in ("*", "/", "%"):
                    advance()
                    rhs = parse_factor()
                    if t[1] == "*":
                        value *= rhs
                    elif t[1] == "/":
                        if rhs == 0:
                            raise ZeroDivisionError("Division by zero")
                        value /= rhs
                    else:
                        value %= rhs
                else:
                    return value

        def parse_factor():
            value = parse_power()
            t = peek()
            if t and t[0] == "op" and t[1] == "^":
                advance()
                rhs = parse_factor()
                value = value ** rhs
            return value

        def parse_power():
            t = peek()
            if t and t[0] == "op" and t[1] == "-":
                advance()
                return -parse_power()
            value = parse_atom()
            while True:
                t = peek()
                if t and t[0] == "op" and t[1] == "!":
                    advance()
                    value = cls._factorial(value)
                else:
                    return value

        def parse_atom():
            t = peek()
            if t is None:
                raise ValueError("Unexpected end of expression")
            if t[0] == "num":
                advance()
                return t[1]
            if t[0] == "op" and t[1] == "(":
                advance()
                value = parse_expr()
                if not (peek() and peek()[0] == "op" and peek()[1] == ")"):
                    raise ValueError("Missing closing parenthesis")
                advance()
                return value
            if t[0] == "ident":
                advance()
                name = t[1]
                if name in cls.SAFE_CONSTS:
                    if peek() and peek()[0] == "op" and peek()[1] == "(":
                        raise ValueError(f"'{name}' is a constant, not a function")
                    return cls.SAFE_CONSTS[name]
                if peek() and peek()[0] == "op" and peek()[1] == "(":
                    advance()
                    args = [parse_expr()]
                    while peek() and peek()[0] == "op" and peek()[1] == ",":
                        advance()
                        args.append(parse_expr())
                    if not (peek() and peek()[0] == "op" and peek()[1] == ")"):
                        raise ValueError("Missing closing parenthesis")
                    advance()
                    func = cls.SAFE_FUNCS.get(name)
                    if func is None:
                        raise ValueError(f"Unknown function: {name}")
                    if name in ("round", "gcd", "fact"):
                        if len(args) != 2 and name == "round":
                            raise ValueError("round(x, ndigits) requires 2 arguments")
                        if name == "round":
                            def _rnd(x, n):
                                return round(x, int(n))
                            func = _rnd
                        else:
                            args = [int(a) for a in args]
                    try:
                        return func(*args)
                    except (ValueError, OverflowError) as e:
                        raise ValueError(f"{name}({', '.join(map(str, args))}) -> {e}") from e
                if name == "x":
                    raise ValueError("Variable 'x' not defined")
                raise ValueError(f"Unknown symbol: {name}")
            if t[0] == "op" and t[1] == ")":
                raise ValueError("Unexpected ')'")
            raise ValueError("Invalid expression")

        if len(tokens) == 1 and tokens[0][0] == "op" and tokens[0][1] == "!":
            raise ValueError("Empty expression")

        result = parse_expr()
        if pos[0] != len(tokens):
            raise ValueError(f"Unexpected trailing tokens: {tokens[pos[0]][1] if tokens[pos[0]][1] != 'err' else '?'}")
        return result


def _fmt_result(value: float) -> str:
    if isinstance(value, complex):
        return str(value)
    if value == float("inf"):
        return "∞"
    if math.isnan(value):  # NaN
        return "NaN"
    if value == 0:
        return "0"
    if abs(value) >= 1e12 or abs(value) < 1e-9:
        return f"{value:.10e}"
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    return text


class MarinerWindow(QMainWindow):
    """Mariner — scientific calculator with history tape."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mariner — Calculator")
        self.resize(760, 620)
        self._history: list[dict] = []
        self._current_expr = ""
        self._load_history()

        self._build_ui()
        self._build_pad()
        self._bind_shortcuts()
        self._refresh_history()

    # ── UI ───────────────────────────────────────────────────
    def _build_ui(self):
        self._status = self.statusBar()
        self._status.setStyleSheet(f"color: {COLORS['text_muted']}; background: {COLORS['deep_navy']}; "
                                   f"font-family: '{FONTS['mono']}'; font-size: {FONTS['size_sm']}px;")

        root = QWidget()
        root.setStyleSheet(f"background: {COLORS['abyss_navy']};")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QWidget()
        top.setStyleSheet(f"background: {COLORS['void_black']}; border-bottom: 1px solid {COLORS['border']};")
        top.setFixedHeight(52)
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(SPACING["lg"], 0, SPACING["lg"], 0)
        brand = QLabel("MARINER")
        brand.setStyleSheet(f"color: {COLORS['seafoam']}; font-family: '{FONTS['mono']}'; "
                            f"font-size: {FONTS['size_lg']}px; font-weight: bold; letter-spacing: 2px; background: transparent;")
        top_lay.addWidget(brand)
        top_lay.addStretch(1)
        hint = QLabel("RPN: not today · functions: sin cos tan sqrt log log10 exp pow abs floor ceil pi e")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px; background: transparent;")
        top_lay.addWidget(hint)
        outer.addWidget(top)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {COLORS['border']}; }}")

        # Left: display + keypad
        left = QWidget()
        left.setStyleSheet(f"background: {COLORS['deep_navy']};")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        left_lay.setSpacing(SPACING["md"])

        self._display = QLineEdit()
        self._display.setReadOnly(True)
        self._display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._display.setText("0")
        self._display.setStyleSheet(f"""
            QLineEdit {{ background: {COLORS['void_black']}; color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']}; padding: 14px 16px;
                font-family: "{FONTS['mono']}"; font-size: 26px; }}
        """)
        left_lay.addWidget(self._display)

        self._expr_label = QLabel("")
        self._expr_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}'; "
                                       f"font-size: {FONTS['size_sm']}px; background: transparent;")
        self._expr_label.setAlignment(Qt.AlignRight)
        left_lay.addWidget(self._expr_label)

        self._keypad = QGridLayout()
        self._keypad.setSpacing(6)
        left_lay.addLayout(self._keypad, 1)
        splitter.addWidget(left)

        # Right: history tape
        right = QWidget()
        right.setStyleSheet(f"background: {COLORS['deep_navy']};")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)
        header = QLabel("  HISTORY")
        header.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; "
                             f"font-size: {FONTS['size_xs']}px; padding: 6px 0; background: {COLORS['deep_navy']}; letter-spacing: 1px;")
        right_lay.addWidget(header)
        self._history_list = QListWidget()
        self._history_list.setStyleSheet(f"""
            QListWidget {{ background: {COLORS['deep_navy']}; border: none; color: {COLORS['hd_white']};
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px; }}
            QListWidget::item {{ padding: 8px 10px; border-bottom: 1px solid {COLORS['border_dim']}; }}
            QListWidget::item:hover {{ background: {COLORS['surface_hover']}; }}
        """)
        self._history_list.itemClicked.connect(self._replay_history)
        right_lay.addWidget(self._history_list, 1)

        clear_btn = self._key("CLEAR", "clear")
        clear_btn.clicked.connect(self._clear_history)
        right_lay.addWidget(clear_btn)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([520, 240])
        outer.addWidget(splitter, 1)

    def _key(self, text: str, kind: str = "num"):
        """Build a keypad button. kind: num, op, fn, eq, misc, clear."""
        if kind == "num":
            bg, fg, hover = COLORS["slate_navy"], COLORS["hd_white"], COLORS["surface_hover"]
        elif kind == "op":
            bg, fg, hover = COLORS["deep_navy"], COLORS["amber"], COLORS["surface_hover"]
        elif kind == "fn":
            bg, fg, hover = COLORS["deep_navy"], COLORS["seafoam"], COLORS["seafoam_deep"]
        elif kind == "eq":
            bg, fg, hover = COLORS["seafoam"], COLORS["void_black"], COLORS["seafoam_dim"]
        elif kind == "clear":
            bg, fg, hover = COLORS["deep_navy"], COLORS["coral"], COLORS["coral_dim"]
        else:
            bg, fg, hover = COLORS["slate_navy"], COLORS["text_secondary"], COLORS["surface_hover"]
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(46)
        btn.setStyleSheet(f"""
            QPushButton {{ background: {bg}; color: {fg}; border: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_md']}px; }}
            QPushButton:hover {{ background: {hover}; border-color: {COLORS['border_active']}; }}
            QPushButton:pressed {{ background: {COLORS['surface_pressed']}; }}
        """)
        return btn

    def _build_pad(self):
        def add(text, kind="num", span=1, slot=None):
            btn = self._key(text, kind)
            if slot is None:
                def _press_slot():
                    self._press(text, kind)
                slot = _press_slot
            btn.clicked.connect(slot)
            self._keypad.addWidget(btn, self._row, self._col, 1, span)
            self._col += span
            if self._col >= 5:
                self._col = 0
                self._row += 1
            return btn

        self._row, self._col = 0, 0
        add("C", "clear", slot=self._clear_display)
        add("⌫", "misc", slot=self._backspace)
        add("(", "op", slot=lambda: self._insert("("))
        add(")", "op", slot=lambda: self._insert(")"))
        add("^", "op", slot=lambda: self._insert("^"))

        add("7")
        add("8")
        add("9")
        add("÷", "op", slot=lambda: self._insert("/"))
        add("√", "fn", slot=self._wrap("sqrt"))

        add("4")
        add("5")
        add("6")
        add("×", "op", slot=lambda: self._insert("*"))
        add("sin", "fn", slot=self._wrap("sin"))

        add("1")
        add("2")
        add("3")
        add("−", "op", slot=lambda: self._insert("-"))
        add("cos", "fn", slot=self._wrap("cos"))

        add("0", span=2)
        add(".")
        add("+", "op", slot=lambda: self._insert("+"))
        add("tan", "fn", slot=self._wrap("tan"))

        add("pi", "fn", slot=self._insert_const("pi"))
        add("e", "fn", slot=self._insert_const("e"))
        add("%", "op", slot=self._insert_mod)
        add("=", "eq", span=2, slot=self._evaluate)

        add("log", "fn", slot=self._wrap("log"))
        add("ln", "fn", slot=self._wrap("ln"))
        add("! ", "fn", slot=self._wrap_factorial)
        add("abs", "fn", slot=self._wrap("abs"))
        add("⌂", "misc", slot=self._replay_last)

    # ── Input handling ───────────────────────────────────────
    def _insert(self, text: str):
        self._current_expr += text
        self._update_display()

    def _wrap(self, name: str):
        def slot():
            if self._current_expr and self._current_expr[-1].isalnum():
                self._current_expr += "*"
            self._current_expr += f"{name}("
            self._update_display()
        return slot

    def _wrap_factorial(self):
        self._current_expr += "!"
        self._update_display()

    def _insert_const(self, name: str):
        def slot():
            if self._current_expr and self._current_expr[-1].isalnum():
                self._current_expr += "*"
            self._current_expr += name
            self._update_display()
        return slot

    def _insert_mod(self):
        if self._current_expr and self._current_expr[-1].isdigit():
            self._current_expr += "%"
        else:
            self._current_expr += "("
        self._update_display()

    def _press(self, text, kind):
        self._insert(text)

    def _backspace(self):
        self._current_expr = self._current_expr[:-1]
        self._update_display()

    def _clear_display(self):
        self._current_expr = ""
        self._display.setText("0")
        self._expr_label.setText("")

    def _update_display(self):
        if not self._current_expr:
            self._display.setText("0")
            self._expr_label.setText("")
            return
        # Live-preview: try to evaluate current expression
        try:
            result = ExpressionEvaluator.evaluate(self._current_expr)
            self._display.setText(_fmt_result(result))
            self._expr_label.setText(self._current_expr)
        except Exception:
            self._display.setText(self._current_expr)
            self._expr_label.setText("")

    # ── Evaluation & history ─────────────────────────────────
    def _evaluate(self):
        expr = self._current_expr.strip()
        if not expr:
            return
        try:
            result = ExpressionEvaluator.evaluate(expr)
            text = _fmt_result(result)
            self._history.insert(0, {"expr": expr, "result": text, "ts": time.time()})
            self._history = self._history[:200]
            self._save_history()
            self._refresh_history()
            self._current_expr = text
            self._display.setText(text)
            self._expr_label.setText(expr)
            self._status.showMessage(f"= {text}")
        except Exception as e:
            self._status.showMessage(f"Error: {e}")
            self._display.setText("ERROR")

    def _replay_history(self, item: QListWidgetItem):
        idx = self._history_list.row(item)
        if 0 <= idx < len(self._history):
            self._current_expr = self._history[idx]["result"]
            self._display.setText(self._current_expr)
            self._expr_label.setText(self._history[idx]["expr"])

    def _replay_last(self):
        if self._history:
            self._current_expr = self._history[0]["result"]
            self._display.setText(self._current_expr)

    def _clear_history(self):
        self._history.clear()
        self._save_history()
        self._refresh_history()

    def _refresh_history(self):
        self._history_list.clear()
        for entry in self._history:
            item = QListWidgetItem(f"  {entry['expr']}  =  {entry['result']}")
            item.setToolTip(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry.get("ts", 0))))
            self._history_list.addItem(item)

    def _load_history(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._history = [e for e in data if isinstance(e, dict) and "expr" in e][:200]
        except (OSError, ValueError):
            self._history = []

    def _save_history(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2)
        except OSError:
            pass

    def _bind_shortcuts(self):
        def shortcut(seq, fn):
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(fn)
            return sc
        shortcut("Return", self._evaluate)
        shortcut("Enter", self._evaluate)
        shortcut("Backspace", self._backspace)
        shortcut("Ctrl+L", self._clear_display)
        shortcut("Ctrl+Backspace", self._clear_display)
        shortcut("Escape", self._clear_display)


def main():
    try:
        log = get_logger("APP")
        log.info("Mariner Calculator starting")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Mariner")
    app.setOrganizationName("Nautilus")

    try:
        from core.icons import get_logo
        app.setWindowIcon(get_logo("mariner"))
    except Exception:
        pass

    try:
        app.setPalette(create_nautilus_palette())
        app.setStyleSheet(get_global_stylesheet())
    except Exception:
        pass

    font = QFont()
    font.setFamilies([FONTS.get("ui", "Segoe UI"), FONTS.get("mono", "JetBrains Mono")])
    font.setPointSize(FONTS.get("size_md", 12))
    app.setFont(font)

    window = MarinerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
