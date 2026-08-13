import os
import re

from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

LANG_EXT_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".xml": "xml",
    ".sql": "sql",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".txt": "text",
    ".pyw": "python",
    ".pyx": "python",
}

LANG_NAMES = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "html": "HTML",
    "css": "CSS",
    "c": "C",
    "cpp": "C++",
    "bash": "Shell Script",
    "json": "JSON",
    "yaml": "YAML",
    "markdown": "Markdown",
    "xml": "XML",
    "sql": "SQL",
    "rust": "Rust",
    "go": "Go",
    "java": "Java",
    "ruby": "Ruby",
    "toml": "TOML",
    "ini": "INI",
    "text": "Plain Text",
}


def detect_language(file_path):
    if not file_path:
        return "text"
    ext = os.path.splitext(file_path)[1].lower()
    return LANG_EXT_MAP.get(ext, "text")


def _fmt(fg=None, bold=False, italic=False, underline=False, bg=None):
    f = QTextCharFormat()
    if fg:
        f.setForeground(QColor(fg))
    if bg:
        f.setBackground(QColor(bg))
    if bold:
        f.setFontWeight(QFont.Bold)
    if italic:
        f.setFontItalic(True)
    if underline:
        f.setFontUnderline(True)
    return f


RULES = {}

# ── Python ──────────────────────────────────────────────
_py_keywords = (
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
    'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
    'while', 'with', 'yield',
)
_py_builtins = (
    'print', 'range', 'len', 'str', 'int', 'float', 'list', 'dict',
    'set', 'tuple', 'input', 'open', 'abs', 'all', 'any', 'bin', 'hex',
    'oct', 'chr', 'ord', 'pow', 'round', 'type', 'super', 'property',
    'staticmethod', 'classmethod', 'isinstance', 'enumerate', 'zip', 'map',
    'filter', 'sorted', 'reversed', 'hasattr', 'getattr', 'setattr',
    'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
    'RuntimeError', 'StopIteration', 'OSError', 'FileNotFoundError',
)

RULES["python"] = [
    (re.compile(r'#.*'), _fmt("#5A7A9C", italic=True)),
] + [
    (re.compile(r'\b' + kw + r'\b'), _fmt("#00F2C2", bold=True))
    for kw in _py_keywords
] + [
    (re.compile(r'\b' + bi + r'\b'), _fmt("#FF7F50"))
    for bi in _py_builtins
] + [
    (re.compile(r'\bself\b'), _fmt("#00F2C2", bold=True, italic=True)),
    (re.compile(r'@\w+'), _fmt("#D4AF37")),
    (re.compile(r'\b[0-9]+(\.[0-9]+)?\b'), _fmt("#FF7F50")),
    (re.compile(r'\b(True|False|None)\b'), _fmt("#00F2C2", bold=True)),
    (re.compile(r'f"""[\s\S]*?"""'), _fmt("#00C9A7")),
    (re.compile(r"f'''[\s\S]*?'''"), _fmt("#00C9A7")),
    (re.compile(r'f"(?:[^"\\]|\\.)*"'), _fmt("#00C9A7")),
    (re.compile(r"f'(?:[^'\\]|\\.)*'"), _fmt("#00C9A7")),
    (re.compile(r'"""[\s\S]*?"""'), _fmt("#4EC9B0")),
    (re.compile(r"'''[\s\S]*?'''"), _fmt("#4EC9B0")),
    (re.compile(r'"(?:[^"\\]|\\.)*"'), _fmt("#4EC9B0")),
    (re.compile(r"'(?:[^'\\]|\\.)*'"), _fmt("#4EC9B0")),
]

# ── JavaScript / TypeScript ─────────────────────────────
_js_keywords = (
    'abstract', 'arguments', 'async', 'await', 'boolean', 'break', 'byte',
    'case', 'catch', 'char', 'class', 'const', 'continue', 'debugger',
    'default', 'delete', 'do', 'double', 'else', 'enum', 'export',
    'extends', 'false', 'final', 'finally', 'float', 'for', 'from',
    'function', 'goto', 'if', 'implements', 'import', 'in', 'instanceof',
    'int', 'interface', 'let', 'long', 'native', 'new', 'null', 'of',
    'package', 'private', 'protected', 'public', 'return', 'short',
    'static', 'super', 'switch', 'synchronized', 'this', 'throw',
    'throws', 'transient', 'true', 'try', 'typeof', 'undefined', 'var',
    'void', 'volatile', 'while', 'with', 'yield',
)
_js_builtins = (
    'console', 'window', 'document', 'Math', 'JSON', 'Promise',
    'Array', 'Object', 'String', 'Number', 'Boolean', 'Symbol',
    'Map', 'Set', 'WeakMap', 'WeakSet', 'Date', 'RegExp', 'Error',
    'TypeError', 'RangeError', 'parseInt', 'parseFloat', 'isNaN',
    'isFinite', 'setTimeout', 'setInterval', 'clearTimeout',
    'clearInterval', 'fetch', 'require', 'module', 'exports',
    'process', 'Buffer', 'global', 'NaN', 'Infinity',
)

_rules_js = [
    (re.compile(r'//.*'), _fmt("#5A7A9C", italic=True)),
    (re.compile(r'/\*[\s\S]*?\*/'), _fmt("#5A7A9C", italic=True)),
] + [
    (re.compile(r'\b' + kw + r'\b'), _fmt("#C586C0", bold=True))
    for kw in _js_keywords
] + [
    (re.compile(r'\b' + bi + r'\b'), _fmt("#4EC9B0"))
    for bi in _js_builtins
] + [
    (re.compile(r'\b[0-9]+(\.[0-9]+)?\b'), _fmt("#B5CEA8")),
    (re.compile(r'"(?:[^"\\]|\\.)*"'), _fmt("#CE9178")),
    (re.compile(r"'(?:[^'\\]|\\.)*'"), _fmt("#CE9178")),
    (re.compile(r'`(?:[^`\\]|\\.)*`'), _fmt("#CE9178")),
    (re.compile(r'\b(const|let|var)\b'), _fmt("#569CD6", bold=True)),
    (re.compile(r'\b(function|=>)\b'), _fmt("#DCDCAA")),
    (re.compile(r'\b(true|false|null|undefined|NaN|Infinity)\b'), _fmt("#569CD6", bold=True)),
]

RULES["javascript"] = _rules_js
RULES["typescript"] = _rules_js

# ── C / C++ ─────────────────────────────────────────────
_c_keywords = (
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
    'inline', 'int', 'long', 'register', 'restrict', 'return', 'short',
    'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef', 'union',
    'unsigned', 'void', 'volatile', 'while',
)
_cpp_extra = (
    'alignas', 'alignof', 'and', 'asm', 'class', 'co_await', 'co_return',
    'co_yield', 'concept', 'const_cast', 'consteval', 'constexpr',
    'constinit', 'decltype', 'delete', 'dynamic_cast', 'explicit',
    'export', 'friend', 'mutable', 'namespace', 'new', 'noexcept',
    'nullptr', 'operator', 'private', 'protected', 'public', 'reinterpret_cast',
    'requires', 'static_assert', 'static_cast', 'template', 'this',
    'thread_local', 'throw', 'try', 'typeid', 'typename', 'using',
    'virtual', 'wchar_t', 'override', 'final',
)
_c_builtins = (
    'printf', 'scanf', 'malloc', 'calloc', 'realloc', 'free', 'strlen',
    'strcpy', 'strncpy', 'strcmp', 'strncmp', 'strcat', 'strncat',
    'memcpy', 'memset', 'memmove', 'memcmp', 'FILE', 'fopen', 'fclose',
    'fread', 'fwrite', 'fprintf', 'fscanf', 'fseek', 'ftell', 'fflush',
    'NULL', 'EOF', 'stdin', 'stdout', 'stderr', 'size_t', 'ptrdiff_t',
    'bool', 'true', 'false', 'string', 'vector', 'map', 'set', 'list',
    'queue', 'stack', 'array', 'unordered_map', 'unordered_set',
    'shared_ptr', 'unique_ptr', 'make_shared', 'make_unique',
    'cout', 'cin', 'cerr', 'endl', 'endl',
)

_rules_c = [
    (re.compile(r'//.*'), _fmt("#5A7A9C", italic=True)),
    (re.compile(r'/\*[\s\S]*?\*/'), _fmt("#5A7A9C", italic=True)),
] + [
    (re.compile(r'\b' + kw + r'\b'), _fmt("#569CD6", bold=True))
    for kw in _c_keywords
] + [
    (re.compile(r'\b' + bi + r'\b'), _fmt("#4EC9B0"))
    for bi in _c_builtins
] + [
    (re.compile(r'\b[0-9]+(\.[0-9]+)?[fFlLuU]*\b'), _fmt("#B5CEA8")),
    (re.compile(r'"(?:[^"\\]|\\.)*"'), _fmt("#CE9178")),
    (re.compile(r"'(?:[^'\\]|\\.)*'"), _fmt("#CE9178")),
    (re.compile(r'#\w+'), _fmt("#C586C0")),
    (re.compile(r'\b(bool|true|false|NULL|nullptr|EOF|sizeof)\b'), _fmt("#569CD6", bold=True)),
]

_rules_cpp = [
    (re.compile(r'//.*'), _fmt("#5A7A9C", italic=True)),
    (re.compile(r'/\*[\s\S]*?\*/'), _fmt("#5A7A9C", italic=True)),
] + [
    (re.compile(r'\b' + kw + r'\b'), _fmt("#569CD6", bold=True))
    for kw in _c_keywords
] + [
    (re.compile(r'\b' + kw + r'\b'), _fmt("#C586C0", bold=True))
    for kw in _cpp_extra
] + [
    (re.compile(r'\b' + bi + r'\b'), _fmt("#4EC9B0"))
    for bi in _c_builtins
] + [
    (re.compile(r'\b[0-9]+(\.[0-9]+)?[fFlLuU]*\b'), _fmt("#B5CEA8")),
    (re.compile(r'"(?:[^"\\]|\\.)*"'), _fmt("#CE9178")),
    (re.compile(r"'(?:[^'\\]|\\.)*'"), _fmt("#CE9178")),
    (re.compile(r'#\w+'), _fmt("#C586C0")),
    (re.compile(r'\b(nullptr|constexpr|consteval|constinit|sizeof|alignof|decltype)\b'), _fmt("#569CD6", bold=True)),
    (re.compile(r'::'), _fmt("#D4D4D4")),
    (re.compile(r'<<|>>'), _fmt("#D4D4D4")),
]

RULES["c"] = _rules_c
RULES["cpp"] = _rules_cpp

# ── HTML / XML ──────────────────────────────────────────
_html_tag = re.compile(r'</?[\w-]+')
_html_attr = re.compile(r'[\w-]+(?==)')
_html_string = re.compile(r'"[^"]*"')
_html_comment = re.compile(r'<!--[\s\S]*?-->')
_html_entity = re.compile(r'&\w+;')

_rules_html = [
    (re.compile(r'<!--[\s\S]*?-->'), _fmt("#6A9955", italic=True)),
    (re.compile(r'<\/?[\w:-]+'), _fmt("#569CD6")),
    (re.compile(r'[\w:-]+(?==)'), _fmt("#9CDCFE")),
    (re.compile(r'"[^"]*"'), _fmt("#CE9178")),
    (re.compile(r"'[^']*'"), _fmt("#CE9178")),
    (re.compile(r'&\w+;'), _fmt("#D7BA7D")),
    (re.compile(r'<!DOCTYPE'), _fmt("#C586C0")),
]

RULES["html"] = _rules_html
RULES["xml"] = _rules_html

# ── CSS ─────────────────────────────────────────────────
_css_prop = re.compile(r'[\w-]+(?=\s*:)')
_css_val = re.compile(r'(?<=:\s)[^;{]+')
_css_selector = re.compile(r'[.#]?[\w:-]+(?=\s*\{)')
_css_comment = re.compile(r'/\*[\s\S]*?\*/')
_css_string = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
_css_unit = re.compile(r'\b\d+(\.\d+)?(px|em|rem|%|vh|vw|s|ms|deg|fr)\b')
_css_color = re.compile(r'#[0-9a-fA-F]{3,8}\b')
_css_at = re.compile(r'@[\w-]+')

_rules_css = [
    (re.compile(r'/\*[\s\S]*?\*/'), _fmt("#6A9955", italic=True)),
    (re.compile(r'@[\w-]+'), _fmt("#C586C0")),
    (re.compile(r'[.#]?[\w:-]+(?=\s*\{)'), _fmt("#D7BA7D")),
    (re.compile(r'[\w-]+(?=\s*:)'), _fmt("#9CDCFE")),
    (re.compile(r':\s*([^;{]+)(?=;)'), _fmt("#CE9178")),
    (re.compile(r'!important'), _fmt("#FF7F50", bold=True)),
    (re.compile(r'\b\d+(\.\d+)?(px|em|rem|%|vh|vw|s|ms|deg|fr)\b'), _fmt("#B5CEA8")),
    (re.compile(r'#[0-9a-fA-F]{3,8}\b'), _fmt("#4EC9B0")),
    (re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''), _fmt("#CE9178")),
    (re.compile(r'\b(important|inherit|initial|unset|none|auto|normal)\b'), _fmt("#569CD6")),
]

RULES["css"] = _rules_css

# ── Shell / Bash ────────────────────────────────────────
_sh_keywords = (
    'if', 'then', 'else', 'elif', 'fi', 'case', 'esac', 'for', 'while',
    'until', 'do', 'done', 'in', 'function', 'return', 'exit', 'local',
    'export', 'source', 'alias', 'unalias', 'echo', 'read', 'shift',
    'set', 'unset', 'trap', 'exec', 'test', 'eval', 'cd', 'pwd', 'pushd',
    'popd', 'dirs', 'true', 'false', 'break', 'continue', 'declare',
    'typeset', 'readonly', 'getopts', 'select', 'time', ' coproc',
)
_sh_builtins = (
    'echo', 'printf', 'read', 'cd', 'pwd', 'pushd', 'popd', 'dirs',
    'let', 'eval', 'exec', 'set', 'unset', 'shift', 'export', 'readonly',
    'declare', 'typeset', 'local', 'trap', 'getopts', 'source', 'builtin',
    'command', 'type', 'hash', 'help', 'umask', 'wait', 'jobs', 'fg',
    'bg', 'disown', 'kill', 'suspend', 'logout', 'exit', 'return',
    'test', 'true', 'false',
)
_sh_special_vars = (
    'HOME', 'USER', 'SHELL', 'PATH', 'PWD', 'OLDPWD', 'TMPDIR', 'LANG',
    'LC_ALL', 'TERM', 'HOSTNAME', 'HOSTTYPE', 'MACHTYPE', 'OSTYPE',
    'BASH', 'BASH_VERSION', 'BASH_SOURCE', 'BASH_REMATCH', 'FUNCNAME',
    'LINENO', 'RANDOM', 'SECONDS', 'PIPESTATUS', 'IFS', 'CDPATH',
    'GLOBIGNORE', 'HISTFILE', 'HISTSIZE', 'HISTFILESIZE', 'PROMPT_COMMAND',
    'PS1', 'PS2', 'PS4', 'BASH_ALIASES', 'BASH_ARGC', 'BASH_ARGV',
    'BASH_CMDS', 'BASH_ENV', 'BASH_EXECUTION_STRING', 'BASH_LINENO',
    'BASH_REMATCH', 'BASH_SUBSHELL', 'BASH_VERSINFO', 'BASH_XTRACEFD',
    'COLORS', 'COLUMNS', 'COMP_WORDBREAKS', 'COMPREPLY', 'DIRSTACK',
    'EUID', 'FUNCNAME', 'GROUPS', 'HISTCMD', 'HOME', 'HOSTNAME',
    'HOSTTYPE', 'IFS', 'IMPORT', 'LANG', 'LC_ALL', 'LC_COLLATE',
    'LC_CTYPE', 'LC_MESSAGES', 'LC_MONETARY', 'LC_NUMERIC', 'LC_TIME',
    'LINENO', 'LINES', 'MACHTYPE', 'MAILCHECK', 'OLDPWD', 'OPTARG',
    'OPTIND', 'OSTYPE', 'PIPESTATUS', 'PPID', 'PROMPT_COMMAND',
    'PS0', 'PS1', 'PS2', 'PS3', 'PS4', 'PWD', 'RANDOM', 'REAL_EUID',
    'SECONDS', 'SHELL', 'SHELLOPTS', 'SHLVL', 'TIMEFORMAT', 'TMPDIR',
    'UID',
)

_rules_sh = [
    (re.compile(r'#.*'), _fmt("#6A9955", italic=True)),
] + [
    (re.compile(r'\b' + kw + r'\b'), _fmt("#C586C0", bold=True))
    for kw in _sh_keywords
] + [
    (re.compile(r'\b' + bi + r'\b'), _fmt("#DCDCAA"))
    for bi in _sh_builtins
] + [
    (re.compile(r'\b' + sv + r'\b'), _fmt("#4FC1FF"))
    for sv in _sh_special_vars
] + [
    (re.compile(r'\$\{?[\w@!#$?*-]+\}?'), _fmt("#4FC1FF", bold=True)),
    (re.compile(r'\$\([^)]*\)'), _fmt("#CE9178")),
    (re.compile(r'`[^`]*`'), _fmt("#CE9178")),
    (re.compile(r'"(?:[^"\\]|\\.)*"'), _fmt("#CE9178")),
    (re.compile(r"'(?:[^'\\]|\\.)*'"), _fmt("#CE9178")),
    (re.compile(r'\b[0-9]+\b'), _fmt("#B5CEA8")),
    (re.compile(r'[|;&><]+'), _fmt("#D4D4D4")),
]

RULES["bash"] = _rules_sh

# ── JSON ────────────────────────────────────────────────
_rules_json = [
    (re.compile(r'"(?:[^"\\]|\\.)*"\s*(?=:)'), _fmt("#9CDCFE")),
    (re.compile(r'"(?:[^"\\]|\\.)*"'), _fmt("#CE9178")),
    (re.compile(r'\b(true|false|null)\b'), _fmt("#569CD6", bold=True)),
    (re.compile(r'\b-?[0-9]+(\.[0-9]+)?([eE][+-]?)?\b'), _fmt("#B5CEA8")),
    (re.compile(r'[{}[\],]'), _fmt("#D4D4D4")),
]

RULES["json"] = _rules_json

# ── YAML ────────────────────────────────────────────────
_rules_yaml = [
    (re.compile(r'#.*'), _fmt("#6A9955", italic=True)),
    (re.compile(r'^[\w.-]+(?=\s*:)', re.MULTILINE), _fmt("#9CDCFE")),
    (re.compile(r'(?<=:\s)(true|false|null|~)\b'), _fmt("#569CD6")),
    (re.compile(r'\b[0-9]+(\.[0-9]+)?\b'), _fmt("#B5CEA8")),
    (re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''), _fmt("#CE9178")),
    (re.compile(r'[|>][+-]?'), _fmt("#C586C0")),
    (re.compile(r'---|\.\.\.'), _fmt("#C586C0", bold=True)),
]

RULES["yaml"] = _rules_yaml

# ── Markdown ────────────────────────────────────────────
_rules_md = [
    (re.compile(r'^#{1,6}\s.*$', re.MULTILINE), _fmt("#569CD6", bold=True)),
    (re.compile(r'\*\*[^*]+\*\*'), _fmt("#D4D4D4", bold=True)),
    (re.compile(r'\*[^*]+\*'), _fmt("#D4D4D4", italic=True)),
    (re.compile(r'__[^_]+__'), _fmt("#D4D4D4", bold=True)),
    (re.compile(r'_[^_]+_'), _fmt("#D4D4D4", italic=True)),
    (re.compile(r'`[^`]+`'), _fmt("#CE9178")),
    (re.compile(r'```[\s\S]*?```'), _fmt("#CE9178")),
    (re.compile(r'\[([^\]]+)\]\([^)]+\)'), _fmt("#4EC9B0", underline=True)),
    (re.compile(r'^[-*+]\s', re.MULTILINE), _fmt("#FF7F50")),
    (re.compile(r'^\d+\.\s', re.MULTILINE), _fmt("#FF7F50")),
    (re.compile(r'^>\s.*$', re.MULTILINE), _fmt("#5A7A9C", italic=True)),
    (re.compile(r'^---+$', re.MULTILINE), _fmt("#5A7A9C")),
    (re.compile(r'\|'), _fmt("#5A7A9C")),
]

RULES["markdown"] = _rules_md


class AbyssalHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language="text"):
        super().__init__(document)
        self.language = language
        self.highlighting_rules = RULES.get(language, [])

    def set_language(self, language):
        self.language = language
        self.highlighting_rules = RULES.get(language, [])
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)
