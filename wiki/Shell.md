# The Shell

The Nautilus desktop shell lives in [`core/main.py`](../core/main.py). It is a
`QMainWindow` (1280×720) composed of a top bar, a central content area, and a
floating dock.

## Components

### `TopBar(QFrame)` — core/main.py:13

A fixed-height (40 px) rounded bar with:

- **Left:** the wordmark `NAUTILUS` — bold mono, letter-spaced 3 px.
- **Right:** a live clock updated every second by a `QTimer`
  (`update_clock()`, format `"hh:mm AP"`).

Both bar and dock use a translucent warm-sand background
(`rgba(212, 200, 176, 200)` — the "glass" effect) over the main background.

### `Dock(QFrame)` — core/main.py:64

A fixed-height (80 px) floating bar holding app launch buttons. Buttons are
built from a simple list:

```python
apps = ["Surfline", "Abyssal", "Kraken"]
```

Each button connects via

```python
btn.clicked.connect(lambda checked, name=app_name: self.on_launch(name))
```

(the `name=app_name` default-argument capture avoids the classic late-binding
lambda bug). Styling covers normal / hover / pressed states from theme tokens.

**Note:** the dock is positioned absolutely at `(440, 650)` relative to the
main window — hardcoded for the default 1280×720 size, not yet anchored on
resize.

### `NautilusShell(QMainWindow)` — core/main.py:106

Owns everything:

| Part | Detail |
| :--- | :--- |
| Window | title "Nautilus OS", 1280×720, warm-sand background |
| Layout | vertical `QVBoxLayout`, zero margins/spacing |
| TopBar | added to layout (row 0) |
| Content | centered `QLabel("Nautilus OS")` title card (placeholder desktop) |
| Dock | parented to the shell, manually placed at (440, 650) |

### `launch_app(app_name)` — core/main.py:144

The dock callback. Only Surfline is wired:

```python
if app_name == "Surfline":
    from apps.surfline.app import SurflineWindow
    self.browser = SurflineWindow()
    self.browser.show()
else:
    print(f"Launching {app_name}...")
```

Abyssal and Kraken buttons exist but only print — they are placeholders for
planned apps ([Roadmap](Roadmap.md)). The import is done lazily inside the
callback so the shell starts fast and doesn't pay WebEngine init cost until a
browser is actually requested.

### `main()` — core/main.py:155

Standard Qt bootstrap: `QApplication` → `NautilusShell().show()` → `app.exec()`.
