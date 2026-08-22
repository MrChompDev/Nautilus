# Surfline Browser

**Surfline** is Nautilus OS's web browser — the first app of the v2 restart.
Source: [`apps/surfline/app.py`](../apps/surfline/app.py), class
`SurflineWindow(QMainWindow)` (1024×680).

It renders web content with **Qt WebEngine** (`QWebEngineView`), which ships
inside PySide6 — no extra pip package needed.

## Layout

Top to bottom:

| Strip | Height | Contents |
| :--- | :--- | :--- |
| Tab bar | 36 px | `bg_dark` strip with a `+` button on the left (stretch keeps it there) |
| Navigation bar | 44 px | `<` back · `>` forward · `↻` reload · URL field · `⌂` home |
| Web view | fill | The single `QWebEngineView` |

## Behaviors

### URL handling — `navigate()` (app.py:172)

The omnibox logic is deliberately simple:

```python
if "." in text and not text.startswith("http"):
    text = "https://" + text            # looks like a domain → https://
elif not text.startswith("http"):
    text = "https://www.google.com/search?q=" + text   # otherwise → Google search
self.web.setUrl(QUrl(text))
```

- Contains a dot → treated as a hostname, prefixed with `https://`.
- Anything else → Google search query.
- Explicit schemes pass through untouched.

### Home page — `home_page()` (app.py:144)

Generated inline HTML themed from `COLORS`/`FONTS`: a centered title, tagline,
a search-style input, and quick links (Google, YouTube, GitHub, Wikipedia in
coral). Loaded via `setHtml()`; the URL bar is cleared.

### Tabs — currently a stub

There's a tab *strip* and a `+` button, but `new_tab()` just re-renders the
home page into the same view (`app.py:169`). Real multi-tab support (one
`QWebEngineView` per tab, switchable) is future work — see [Roadmap](Roadmap.md).

### Sync — `update_url()`

`web.urlChanged` writes the current URL back into the omnibox so it always
reflects the visible page.

## Notes & gotchas

- The view is created **before** `home_page()` is first called
  (`app.py:137-142`) — ordering matters because `setHtml` needs the widget.
- Buttons are minimal glyph labels (`<`, `>`, `↻`, `⌂`) styled via a shared
  `btn_style` f-string; hover uses the theme `hover` surface color.
- The module has no `if __name__ == "__main__"` block yet — today Surfline is
  launched by the shell ([Shell](Shell.md)); standalone launching would need an
  entry point added.

See [Architecture](Architecture.md) for how apps bootstrap, and
[Design System](Design-System.md) for the styling rules it follows.
