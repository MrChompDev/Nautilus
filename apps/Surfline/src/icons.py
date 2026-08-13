"""
Surfline SVG Icons - Procedurally generated flat icons.
No emojis, no external assets required.
"""
import os


def _write_svg(filename, content):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def generate_all_icons():
    _write_svg("back.svg", _icon_back())
    _write_svg("forward.svg", _icon_forward())
    _write_svg("reload.svg", _icon_reload())
    _write_svg("stop.svg", _icon_stop())
    _write_svg("home.svg", _icon_home())
    _write_svg("new_tab.svg", _icon_new_tab())
    _write_svg("close_tab.svg", _icon_close_tab())
    _write_svg("shield.svg", _icon_shield())
    _write_svg("terminal.svg", _icon_terminal())
    _write_svg("profile.svg", _icon_profile())
    _write_svg("menu.svg", _icon_menu())
    _write_svg("bookmark.svg", _icon_bookmark())
    _write_svg("settings.svg", _icon_settings())
    _write_svg("find.svg", _icon_find())


def _icon_back():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M10 3L5 8L10 13" stroke="#00F2C2" stroke-width="2" fill="none" stroke-linecap="square"/></svg>'


def _icon_forward():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M6 3L11 8L6 13" stroke="#00F2C2" stroke-width="2" fill="none" stroke-linecap="square"/></svg>'


def _icon_reload():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M3 8A5 5 0 0 1 13 8" stroke="#00F2C2" stroke-width="2" fill="none" stroke-linecap="square"/><path d="M13 8A5 5 0 0 1 3 8" stroke="#00F2C2" stroke-width="2" fill="none" stroke-linecap="square" opacity="0.4"/><path d="M13 4L13 8L17 8" stroke="#00F2C2" stroke-width="2" fill="none" stroke-linecap="square" transform="translate(-2,-1)"/></svg>'


def _icon_stop():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><rect x="3" y="3" width="10" height="10" fill="#FF4757" rx="0"/></svg>'


def _icon_home():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M2 8L8 2L14 8" stroke="#00F2C2" stroke-width="2" fill="none" stroke-linecap="square"/><path d="M4 7V14H6V10H10V14H12V7" stroke="#00F2C2" stroke-width="2" fill="none" stroke-linecap="square"/></svg>'


def _icon_new_tab():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><rect x="3" y="3" width="10" height="10" stroke="#00F2C2" stroke-width="1.5" fill="none"/><line x1="8" y1="5" x2="8" y2="11" stroke="#00F2C2" stroke-width="1.5"/><line x1="5" y1="8" x2="11" y2="8" stroke="#00F2C2" stroke-width="1.5"/></svg>'


def _icon_close_tab():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><line x1="4" y1="4" x2="12" y2="12" stroke="#8899AA" stroke-width="1.5"/><line x1="12" y1="4" x2="4" y2="12" stroke="#8899AA" stroke-width="1.5"/></svg>'


def _icon_shield():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M8 1L2 4V8C2 11 5 14 8 15C11 14 14 11 14 8V4L8 1Z" stroke="#00F2C2" stroke-width="1.5" fill="none"/><path d="M5 8L7 10L11 6" stroke="#00F2C2" stroke-width="1.5" fill="none"/></svg>'


def _icon_terminal():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="3" width="12" height="10" stroke="#00F2C2" stroke-width="1.5" fill="none"/><path d="M5 7L7 9L5 11" stroke="#00F2C2" stroke-width="1.5" fill="none"/><line x1="8" y1="11" x2="11" y2="11" stroke="#00F2C2" stroke-width="1.5"/></svg>'


def _icon_profile():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="5" r="3" stroke="#00F2C2" stroke-width="1.5" fill="none"/><path d="M2 14C2 11 5 9 8 9C11 9 14 11 14 14" stroke="#00F2C2" stroke-width="1.5" fill="none"/></svg>'


def _icon_menu():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><line x1="3" y1="4" x2="13" y2="4" stroke="#00F2C2" stroke-width="1.5"/><line x1="3" y1="8" x2="13" y2="8" stroke="#00F2C2" stroke-width="1.5"/><line x1="3" y1="12" x2="13" y2="12" stroke="#00F2C2" stroke-width="1.5"/></svg>'


def _icon_bookmark():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M4 2H12V14L8 11L4 14V2Z" stroke="#00F2C2" stroke-width="1.5" fill="none"/></svg>'


def _icon_settings():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="2" stroke="#00F2C2" stroke-width="1.5" fill="none"/><path d="M8 1V3M8 13V15M1 8H3M13 8H15M3 3L5 5M11 11L13 13M13 3L11 5M5 11L3 13" stroke="#00F2C2" stroke-width="1.5"/></svg>'


def _icon_find():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><circle cx="6" cy="6" r="4" stroke="#00F2C2" stroke-width="1.5" fill="none"/><line x1="9" y1="9" x2="14" y2="14" stroke="#00F2C2" stroke-width="1.5"/></svg>'


def icon_path(name):
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", f"{name}.svg")


def ensure_icons():
    generate_all_icons()
