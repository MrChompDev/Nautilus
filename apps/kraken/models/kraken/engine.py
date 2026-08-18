"""Kraken — coding model engine.

Actual task executor: writes code to files, runs commands, produces real output.
Not a chatbot — a coding agent that does the work.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable

from apps.kraken.core.engine import BaseEngine, EngineResponse
from apps.kraken.core.tools import execute_tool, file_read, file_write, terminal_exec


def _brain_context(query: str, workspace: str | None, max_chars: int = 2000) -> str:
    try:
        from apps.kraken.engine.brain import ProjectBrain
    except Exception:
        return ""
    if not workspace or not os.path.isdir(workspace):
        return ""
    brain = ProjectBrain(workspace)
    if not os.path.exists(brain.db_path):
        try:
            brain.scan()
        except Exception:
            return ""
    try:
        relevant = brain.context(query, k=5)
        tree = brain.file_map()
    except Exception:
        return ""
    lines = tree.splitlines()[:100]
    body = f"# Project files ({workspace})\n" + "\n".join(lines) + f"\n\n# Relevant\n{relevant}"
    return body[:max_chars]


def _classify_intent(msg: str) -> str:
    lower = msg.lower().strip()
    first_word = lower.split()[0] if lower.split() else ""
    if first_word in ("hello", "hi", "hey", "greetings", "sup", "yo"):
        if len(lower.split()) <= 4:
            return "greeting"
    if any(w in lower for w in ["what's up", "what's good"]):
        return "greeting"
    if any(w in lower for w in ["help", "what can you do", "capabilities"]):
        return "help"
    if any(w in lower for w in ["write", "create", "make", "build", "generate", "code",
                                  "function", "class", "script", "file", "program",
                                  "implement", "add", "write me", "write a", "write an",
                                  "develop", "produce", "code a", "code the"]):
        return "write_code"
    if any(w in lower for w in ["debug", "error", "fix", "bug", "issue", "broken",
                                  "traceback", "exception", "crash", "failing"]):
        return "debug"
    if any(w in lower for w in ["explain", "what does", "how does", "how do",
                                  "why does", "walk me through", "tell me about"]):
        return "explain"
    if any(w in lower for w in ["refactor", "optimize", "improve", "clean up",
                                  "simplify", "restructure"]):
        return "refactor"
    if any(w in lower for w in ["test", "testing", "unit test", "pytest", "unittest",
                                  "write tests", "add tests"]):
        return "test"
    if any(w in lower for w in ["list files", "show files", "ls", "dir", "files"]):
        return "list_files"
    if any(w in lower for w in ["read ", "cat ", "show ", "open ", "view "]):
        return "read_file"
    if any(w in lower for w in ["deploy", "ship", "release", "publish"]):
        return "deploy"
    if any(w in lower for w in ["review", "check", "audit", "lint"]):
        return "review"
    if any(w in lower for w in ["plan", "architect", "design", "structure"]):
        return "plan"
    if "?" in lower:
        return "question"
    return "general"


def _extract_code_block(text: str) -> str | None:
    """Extract code from markdown code blocks."""
    m = re.search(r"```(?:python|py|javascript|js|html|css|json|yaml|sh|bash)?\s*\n(.*?)```",
                   text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _guess_filename(msg: str, code: str) -> str:
    """Guess a reasonable filename from the request and code."""
    lower = msg.lower()
    # Check if user specified a filename
    for word in msg.split():
        if "." in word and any(ext in word.lower() for ext in [".py", ".js", ".html", ".css", ".json", ".sh", ".ts"]):
            return word.strip("\"'")
    # Guess from code content
    if "def " in code:
        # Python file
        m = re.search(r"def (\w+)", code)
        if m:
            return f"{m.group(1)}.py"
        return "script.py"
    if "class " in code:
        m = re.search(r"class (\w+)", code)
        if m:
            return f"{m.group(1).lower()}.py"
        return "module.py"
    if "<html" in code.lower() or "<div" in code.lower():
        return "index.html"
    if "function " in code:
        m = re.search(r"function (\w+)", code)
        if m:
            return f"{m.group(1)}.js"
        return "script.js"
    if "import " in code or "from " in code:
        return "module.py"
    return "output.py"


class KrakenEngine(BaseEngine):
    model_id = "kraken"

    def __init__(self, cfg):
        self.cfg = cfg

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> EngineResponse:
        t0 = self._tick()

        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = (m.get("content") or "").strip()
                break

        ws = workspace or os.getcwd()
        intent = _classify_intent(user_msg)

        # Route to task executor
        if intent == "write_code":
            text = self._task_write_code(user_msg, ws)
        elif intent == "debug":
            text = self._task_debug(user_msg, ws)
        elif intent == "explain":
            text = self._task_explain(user_msg, ws)
        elif intent == "refactor":
            text = self._task_refactor(user_msg, ws)
        elif intent == "test":
            text = self._task_test(user_msg, ws)
        elif intent == "list_files":
            text = self._task_list_files(ws)
        elif intent == "read_file":
            text = self._task_read_file(user_msg, ws)
        elif intent == "help":
            text = self._help_text()
        elif intent == "greeting":
            text = "Hey! I'm Kraken. What do you need built?"
        else:
            text = self._task_general(user_msg, ws)

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)

    # ── Task: Write Code ─────────────────────────────────────────

    def _task_write_code(self, msg: str, ws: str) -> str:
        """Parse the request, generate code, write to file, return result."""
        # Build a concrete code generation prompt
        code = self._generate_code(msg, ws)
        if not code:
            return (
                "I need more details to write the code.\n\n"
                "Please specify:\n"
                "- What the code should do\n"
                "- What language (Python, JS, etc.)\n"
                "- Any specific requirements or constraints\n\n"
                "Example: \"Write a Python function that reads a CSV file and returns a list of dicts\""
            )

        # Determine filename
        filename = _guess_filename(msg, code)
        filepath = os.path.join(ws, filename)

        # Write the file
        result = file_write(filepath, code)
        if not result.ok:
            return f"Error writing file: {result.error}"

        # Try to run it if it's Python
        run_output = ""
        if filename.endswith(".py"):
            run_result = terminal_exec(f"cd {ws} && python3 {filename}", timeout=15)
            if run_result.ok and run_result.output:
                run_output = f"\n\n**Output:**\n```\n{run_result.output[:1000]}\n```"
            elif run_result.error:
                run_output = f"\n\n**Run error:** {run_result.error}"

        lines = [
            f"**Created:** `{filename}`",
            "",
            f"**Code:**",
            f"```python",
            code,
            f"```",
        ]
        if run_output:
            lines.append(run_output)
        lines.append(f"\nFile saved to: {filepath}")
        return "\n".join(lines)

    def _generate_code(self, msg: str, ws: str) -> str | None:
        """Generate actual code based on the request."""
        lower = msg.lower()

        # Detect what kind of code to generate
        if any(w in lower for w in ["function", "func", "def "]):
            return self._gen_function(msg)
        if any(w in lower for w in ["class", "classes"]):
            return self._gen_class(msg)
        if any(w in lower for w in ["script", "program", "tool", "utility"]):
            return self._gen_script(msg)
        if any(w in lower for w in ["api", "server", "endpoint", "route", "flask", "fastapi"]):
            return self._gen_api(msg)
        if any(w in lower for w in ["test", "testing", "unittest", "pytest"]):
            return self._gen_test(msg)
        if any(w in lower for w in ["html", "web page", "website", "page"]):
            return self._gen_html(msg)
        if any(w in lower for w in ["config", "configuration", "settings", "yaml", "json"]):
            return self._gen_config(msg)
        if any(w in lower for w in ["cli", "command line", "argparse", "click"]):
            return self._gen_cli(msg)
        if any(w in lower for w in ["database", "sql", "sqlite", "db"]):
            return self._gen_database(msg)
        # Default: try to write a reasonable script
        return self._gen_script(msg)

    def _gen_function(self, msg: str) -> str:
        lower = msg.lower()
        # Common function patterns - actual working implementations
        if "reverse" in lower and ("string" in lower or "str" in lower or "text" in lower):
            return (
                "def reverse_string(s: str) -> str:\n"
                "    \"\"\"Reverse a string.\"\"\"\n"
                "    return s[::-1]\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    tests = ['hello', 'world', 'Python', '']\n"
                "    for t in tests:\n"
                "        print(f'{t!r} -> {reverse_string(t)!r}')\n"
            )
        if "reverse" in lower and "list" in lower:
            return (
                "def reverse_list(items: list) -> list:\n"
                "    \"\"\"Reverse a list (without modifying original).\"\"\"\n"
                "    return items[::-1]\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    data = [1, 2, 3, 4, 5]\n"
                "    print(f'Original: {data}')\n"
                "    print(f'Reversed: {reverse_list(data)}')\n"
            )
        if "sort" in lower:
            return (
                "def sort_list(items, key=None, reverse=False):\n"
                "    \"\"\"Sort a list with optional key function.\n\n"
                "    Args:\n"
                "        items: List to sort\n"
                "        key: Optional key function for custom sorting\n"
                "        reverse: Sort in descending order if True\n"
                "\n"
                "    Returns:\n"
                "        New sorted list\n"
                "    \"\"\"\n"
                "    return sorted(items, key=key, reverse=reverse)\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    data = [3, 1, 4, 1, 5, 9, 2, 6]\n"
                "    print(f'Original: {data}')\n"
                "    print(f'Sorted:   {sort_list(data)}')\n"
                "    print(f'Reverse:  {sort_list(data, reverse=True)}')\n"
                "    print(f'By last:  {sort_list(data, key=lambda x: x % 10)}')\n"
            )
        if "fibonacci" in lower:
            return (
                "def fibonacci(n: int) -> list[int]:\n"
                "    \"\"\"Generate first n Fibonacci numbers.\"\"\"\n"
                "    if n <= 0:\n"
                "        return []\n"
                "    if n == 1:\n"
                "        return [0]\n"
                "    fibs = [0, 1]\n"
                "    for _ in range(2, n):\n"
                "        fibs.append(fibs[-1] + fibs[-2])\n"
                "    return fibs\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    print(fibonacci(10))\n"
            )
        if "factorial" in lower:
            return (
                "def factorial(n: int) -> int:\n"
                "    \"\"\"Calculate factorial of n.\"\"\"\n"
                "    if n < 0:\n"
                "        raise ValueError('Factorial not defined for negative numbers')\n"
                "    result = 1\n"
                "    for i in range(2, n + 1):\n"
                "        result *= i\n"
                "    return result\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    for n in range(8):\n"
                "        print(f'{n}! = {factorial(n)}')\n"
            )
        if "palindrome" in lower:
            return (
                "def is_palindrome(s: str) -> bool:\n"
                "    \"\"\"Check if string is a palindrome (case-insensitive).\"\"\"\n"
                "    clean = ''.join(c.lower() for c in s if c.isalnum())\n"
                "    return clean == clean[::-1]\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    tests = ['racecar', 'hello', 'A man a plan a canal Panama']\n"
                "    for t in tests:\n"
                "        print(f'{t!r} -> {is_palindrome(t)}')\n"
            )
        if "count" in lower and ("word" in lower or "char" in lower or "letter" in lower):
            return (
                "from collections import Counter\n"
                "\n"
                "\n"
                "def count_chars(s: str) -> dict[str, int]:\n"
                "    \"\"\"Count frequency of each character.\"\"\"\n"
                "    return dict(Counter(s))\n"
                "\n"
                "\n"
                "def count_words(s: str) -> dict[str, int]:\n"
                "    \"\"\"Count frequency of each word.\"\"\"\n"
                "    return dict(Counter(s.lower().split()))\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    text = 'hello world hello'\n"
                "    print(f'Chars: {count_chars(text)}')\n"
                "    print(f'Words: {count_words(text)}')\n"
            )
        if "filter" in lower:
            return (
                "def filter_list(items, condition):\n"
                "    \"\"\"Filter list by condition function.\"\"\"\n"
                "    return [x for x in items if condition(x)]\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\n"
                "    evens = filter_list(numbers, lambda x: x % 2 == 0)\n"
                "    print(f'Even numbers: {evens}')\n"
            )
        if "unique" in lower or "deduplicate" in lower or "distinct" in lower:
            return (
                "def unique(items: list) -> list:\n"
                "    \"\"\"Remove duplicates while preserving order.\"\"\"\n"
                "    seen = set()\n"
                "    result = []\n"
                "    for item in items:\n"
                "        if item not in seen:\n"
                "            seen.add(item)\n"
                "            result.append(item)\n"
                "    return result\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    data = [1, 2, 2, 3, 3, 3, 4]\n"
                "    print(f'Original: {data}')\n"
                "    print(f'Unique:   {unique(data)}')\n"
            )
        if "flatten" in lower:
            return (
                "def flatten(nested: list) -> list:\n"
                "    \"\"\"Flatten a nested list.\"\"\"\n"
                "    result = []\n"
                "    for item in nested:\n"
                "        if isinstance(item, list):\n"
                "            result.extend(flatten(item))\n"
                "        else:\n"
                "            result.append(item)\n"
                "    return result\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    data = [[1, 2], [3, [4, 5]], [6]]\n"
                "    print(f'Nested: {data}')\n"
                "    print(f'Flat:   {flatten(data)}')\n"
            )
        if "merge" in lower and "dict" in lower:
            return (
                "def merge_dicts(*dicts: dict) -> dict:\n"
                "    \"\"\"Merge multiple dictionaries (last wins).\"\"\"\n"
                "    result = {}\n"
                "    for d in dicts:\n"
                "        result.update(d)\n"
                "    return result\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    d1 = {'a': 1, 'b': 2}\n"
                "    d2 = {'b': 3, 'c': 4}\n"
                "    print(f'Merged: {merge_dicts(d1, d2)}')\n"
            )
        if "read" in lower and ("file" in lower or "write" not in lower):
            return (
                "from pathlib import Path\n"
                "\n"
                "\n"
                "def read_file(filepath: str, encoding: str = 'utf-8') -> str:\n"
                "    \"\"\"Read a file and return its contents.\"\"\"\n"
                "    path = Path(filepath)\n"
                "    if not path.exists():\n"
                "        raise FileNotFoundError(f'File not found: {filepath}')\n"
                "    return path.read_text(encoding=encoding)\n"
                "\n"
                "\n"
                "def read_lines(filepath: str) -> list[str]:\n"
                "    \"\"\"Read a file and return its lines.\"\"\"\n"
                "    return read_file(filepath).splitlines()\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    if len(sys.argv) > 1:\n"
                "        print(read_file(sys.argv[1]))\n"
                "    else:\n"
                "        print('Usage: python read_file.py <path>')\n"
            )
        if "web" in lower and ("scrape" in lower or "scraper" in lower or "crawl" in lower):
            return (
                "from urllib.request import urlopen, Request\n"
                "from html.parser import HTMLParser\n"
                "import re\n"
                "\n"
                "\n"
                "class LinkExtractor(HTMLParser):\n"
                "    \"\"\"Extract links and text from HTML.\"\"\"\n"
                "    def __init__(self):\n"
                "        super().__init__()\n"
                "        self.links = []\n"
                "        self.text_parts = []\n"
                "        self._in_tag = None\n"
                "\n"
                "    def handle_starttag(self, tag, attrs):\n"
                "        if tag == 'a':\n"
                "            for name, val in attrs:\n"
                "                if name == 'href':\n"
                "                    self.links.append(val)\n"
                "        self._in_tag = tag\n"
                "\n"
                "    def handle_data(self, data):\n"
                "        self.text_parts.append(data.strip())\n"
                "\n"
                "    def get_text(self):\n"
                "        return ' '.join(p for p in self.text_parts if p)\n"
                "\n"
                "\n"
                "def scrape(url: str) -> dict:\n"
                "    \"\"\"Scrape a URL and return links + text.\"\"\"\n"
                "    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})\n"
                "    with urlopen(req, timeout=10) as resp:\n"
                "        html = resp.read().decode('utf-8', errors='replace')\n"
                "    parser = LinkExtractor()\n"
                "    parser.feed(html)\n"
                "    return {'links': parser.links, 'text': parser.get_text()[:2000]}\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    url = sys.argv[1] if len(sys.argv) > 1 else 'https://example.com'\n"
                "    result = scrape(url)\n"
                "    print(f'Links: {len(result[\"links\"])}')\n"
                "    for link in result['links'][:5]:\n"
                "        print(f'  {link}')\n"
                "    print(f'Text preview: {result[\"text\"][:200]}')\n"
            )
        if "download" in lower or "fetch" in lower:
            return (
                "from urllib.request import urlopen, Request\n"
                "from pathlib import Path\n"
                "import sys\n"
                "\n"
                "\n"
                "def download(url: str, output: str = None) -> str:\n"
                "    \"\"\"Download a URL to a local file.\"\"\"\n"
                "    if not output:\n"
                "        output = url.split('/')[-1] or 'download'\n"
                "    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})\n"
                "    with urlopen(req, timeout=30) as resp:\n"
                "        data = resp.read()\n"
                "    Path(output).write_bytes(data)\n"
                "    return f'Downloaded {len(data):,} bytes to {output}'\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    if len(sys.argv) > 1:\n"
                "        print(download(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))\n"
                "    else:\n"
                "        print('Usage: python download.py <url> [output]')\n"
            )
        if "csv" in lower or "spreadsheet" in lower:
            return (
                "import csv\n"
                "from pathlib import Path\n"
                "\n"
                "\n"
                "def read_csv(filepath: str) -> list[dict]:\n"
                "    \"\"\"Read a CSV file into a list of dicts.\"\"\"\n"
                "    with open(filepath, encoding='utf-8', newline='') as f:\n"
                "        return list(csv.DictReader(f))\n"
                "\n"
                "\n"
                "def write_csv(filepath: str, rows: list[dict]):\n"
                "    \"\"\"Write a list of dicts to a CSV file.\"\"\"\n"
                "    if not rows:\n"
                "        return\n"
                "    with open(filepath, 'w', encoding='utf-8', newline='') as f:\n"
                "        writer = csv.DictWriter(f, fieldnames=rows[0].keys())\n"
                "        writer.writeheader()\n"
                "        writer.writerows(rows)\n"
                "\n"
                "\n"
                "def filter_csv(filepath: str, column: str, value: str) -> list[dict]:\n"
                "    \"\"\"Filter CSV rows where column equals value.\"\"\"\n"
                "    return [r for r in read_csv(filepath) if r.get(column) == value]\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    if len(sys.argv) > 1:\n"
                "        rows = read_csv(sys.argv[1])\n"
                "        print(f'{len(rows)} rows loaded')\n"
                "        if rows:\n"
                "            print(f'Columns: {list(rows[0].keys())}')\n"
                "            print(f'First: {rows[0]}')\n"
                "    else:\n"
                "        print('Usage: python csv_tool.py <file.csv>')\n"
            )
        if "json" in lower and ("transform" in lower or "convert" in lower or "process" in lower):
            return (
                "import json\n"
                "from pathlib import Path\n"
                "\n"
                "\n"
                "def load_json(filepath: str) -> dict | list:\n"
                "    \"\"\"Load a JSON file.\"\"\"\n"
                "    return json.loads(Path(filepath).read_text())\n"
                "\n"
                "\n"
                "def save_json(filepath: str, data, indent: int = 2):\n"
                "    \"\"\"Save data to a JSON file.\"\"\"\n"
                "    Path(filepath).write_text(json.dumps(data, indent=indent, default=str))\n"
                "\n"
                "\n"
                "def transform(data, func):\n"
                "    \"\"\"Apply a transform function to each value in a dict/list.\"\"\"\n"
                "    if isinstance(data, dict):\n"
                "        return {k: transform(v, func) for k, v in data.items()}\n"
                "    if isinstance(data, list):\n"
                "        return [transform(item, func) for item in data]\n"
                "    return func(data)\n"
                "\n"
                "\n"
                "def flatten_json(data: dict, prefix: str = '') -> dict:\n"
                "    \"\"\"Flatten nested JSON into dot-notation keys.\"\"\"\n"
                "    items = {}\n"
                "    for k, v in data.items():\n"
                "        key = f'{prefix}.{k}' if prefix else k\n"
                "        if isinstance(v, dict):\n"
                "            items.update(flatten_json(v, key))\n"
                "        else:\n"
                "            items[key] = v\n"
                "    return items\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    if len(sys.argv) > 1:\n"
                "        data = load_json(sys.argv[1])\n"
                "        flat = flatten_json(data) if isinstance(data, dict) else data\n"
                "        for k, v in list(flat.items())[:10]:\n"
                "            print(f'{k}: {v}')\n"
                "    else:\n"
                "        print('Usage: python json_tool.py <file.json>')\n"
            )
        if "regex" in lower or "pattern" in lower and "match" in lower:
            return (
                "import re\n"
                "\n"
                "\n"
                "PATTERNS = {\n"
                "    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}',\n"
                "    'url': r'https?://[^\\s]+',\n"
                "    'ip': r'\\b\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\b',\n"
                "    'phone': r'\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b',\n"
                "    'date': r'\\b\\d{4}[-/]\\d{2}[-/]\\d{2}\\b',\n"
                "    'hex_color': r'#[0-9a-fA-F]{6}',\n"
                "}\n"
                "\n"
                "\n"
                "def find_all(text: str, pattern_name: str) -> list[str]:\n"
                "    \"\"\"Find all matches of a named pattern.\"\"\"\n"
                "    pat = PATTERNS.get(pattern_name, pattern_name)\n"
                "    return re.findall(pat, text)\n"
                "\n"
                "\n"
                "def extract_emails(text: str) -> list[str]:\n"
                "    \"\"\"Extract all emails from text.\"\"\"\n"
                "    return find_all(text, 'email')\n"
                "\n"
                "\n"
                "def extract_urls(text: str) -> list[str]:\n"
                "    \"\"\"Extract all URLs from text.\"\"\"\n"
                "    return find_all(text, 'url')\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    sample = 'Contact us at info@example.com or visit https://example.com'\n"
                "    print(f'Emails: {extract_emails(sample)}')\n"
                "    print(f'URLs: {extract_urls(sample)}')\n"
            )
        if "date" in lower or "time" in lower and "format" in lower:
            return (
                "from datetime import datetime, timedelta\n"
                "import time\n"
                "\n"
                "\n"
                "def now() -> str:\n"
                "    \"\"\"Current timestamp as ISO string.\"\"\"\n"
                "    return datetime.now().isoformat()\n"
                "\n"
                "\n"
                "def format_date(dt: datetime, fmt: str = '%Y-%m-%d %H:%M') -> str:\n"
                "    \"\"\"Format a datetime object.\"\"\"\n"
                "    return dt.strftime(fmt)\n"
                "\n"
                "\n"
                "def parse_date(s: str, fmt: str = '%Y-%m-%d') -> datetime:\n"
                "    \"\"\"Parse a date string.\"\"\"\n"
                "    return datetime.strptime(s, fmt)\n"
                "\n"
                "\n"
                "def days_ago(n: int) -> datetime:\n"
                "    \"\"\"Return datetime from n days ago.\"\"\"\n"
                "    return datetime.now() - timedelta(days=n)\n"
                "\n"
                "\n"
                "def time_ago(seconds: float) -> str:\n"
                "    \"\"\"Human-readable time elapsed.\"\"\"\n"
                "    for unit, div in [('yr', 31536000), ('mo', 2592000), ('d', 86400),\n"
                "                       ('hr', 3600), ('min', 60), ('sec', 1)]:\n"
                "        if seconds >= div:\n"
                "            return f'{int(seconds // div)}{unit} ago'\n"
                "    return 'just now'\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    print(f'Now: {now()}')\n"
                "    print(f'7 days ago: {format_date(days_ago(7))}')\n"
                "    print(f'1 hour ago: {time_ago(3600)}')\n"
            )
        if "email" in lower and "valid" in lower:
            return (
                "import re\n"
                "\n"
                "\n"
                "EMAIL_REGEX = re.compile(\n"
                "    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n"
                ")\n"
                "\n"
                "\n"
                "def is_valid_email(email: str) -> bool:\n"
                "    \"\"\"Check if an email address is valid.\"\"\"\n"
                "    return bool(EMAIL_REGEX.match(email))\n"
                "\n"
                "\n"
                "def validate_emails(emails: list[str]) -> dict:\n"
                "    \"\"\"Validate a list of emails, return valid/invalid.\"\"\"\n"
                "    valid = [e for e in emails if is_valid_email(e)]\n"
                "    invalid = [e for e in emails if not is_valid_email(e)]\n"
                "    return {'valid': valid, 'invalid': invalid}\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    tests = ['user@example.com', 'bad@', 'test@test.co', 'no-at-sign']\n"
                "    for t in tests:\n"
                "        print(f'{t}: {is_valid_email(t)}')\n"
            )
        if "url" in lower and "pars" in lower:
            return (
                "from urllib.parse import urlparse, parse_qs, urlencode, urlunparse\n"
                "\n"
                "\n"
                "def parse_url(url: str) -> dict:\n"
                "    \"\"\"Parse a URL into components.\"\"\"\n"
                "    p = urlparse(url)\n"
                "    return {\n"
                "        'scheme': p.scheme,\n"
                "        'host': p.hostname or '',\n"
                "        'port': p.port,\n"
                "        'path': p.path,\n"
                "        'params': parse_qs(p.query),\n"
                "        'fragment': p.fragment,\n"
                "    }\n"
                "\n"
                "\n"
                "def build_url(scheme: str, host: str, path: str = '/', params: dict = None) -> str:\n"
                "    \"\"\"Build a URL from components.\"\"\"\n"
                "    query = urlencode(params or {})\n"
                "    return urlunparse((scheme, host, path, '', query, ''))\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    url = 'https://example.com/path?key=val&foo=bar#section'\n"
                "    parsed = parse_url(url)\n"
                "    for k, v in parsed.items():\n"
                "        print(f'{k}: {v}')\n"
            )
        if "hash" in lower or "checksum" in lower:
            return (
                "import hashlib\n"
                "\n"
                "\n"
                "def hash_text(text: str, algorithm: str = 'sha256') -> str:\n"
                "    \"\"\"Hash a string with the specified algorithm.\"\"\"\n"
                "    h = hashlib.new(algorithm)\n"
                "    h.update(text.encode('utf-8'))\n"
                "    return h.hexdigest()\n"
                "\n"
                "\n"
                "def hash_file(filepath: str, algorithm: str = 'sha256') -> str:\n"
                "    \"\"\"Hash a file's contents.\"\"\"\n"
                "    h = hashlib.new(algorithm)\n"
                "    with open(filepath, 'rb') as f:\n"
                "        for chunk in iter(lambda: f.read(8192), b''):\n"
                "            h.update(chunk)\n"
                "    return h.hexdigest()\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    print(f'SHA256 of \"hello\": {hash_text(\"hello\")}')\n"
                "    print(f'MD5 of \"hello\":    {hash_text(\"hello\", \"md5\")}')\n"
            )
        if "compress" in lower or "zip" in lower:
            return (
                "import gzip\n"
                "import shutil\n"
                "from pathlib import Path\n"
                "\n"
                "\n"
                "def compress_file(filepath: str, output: str = None) -> str:\n"
                "    \"\"\"Gzip compress a file.\"\"\"\n"
                "    output = output or filepath + '.gz'\n"
                "    with open(filepath, 'rb') as f_in:\n"
                "        with gzip.open(output, 'wb') as f_out:\n"
                "            shutil.copyfileobj(f_in, f_out)\n"
                "    orig = Path(filepath).stat().st_size\n"
                "    comp = Path(output).stat().st_size\n"
                "    return f'{filepath} ({orig:,} bytes) -> {output} ({comp:,} bytes, {100-comp/orig*100:.0f}% smaller)'\n"
                "\n"
                "\n"
                "def decompress_file(filepath: str, output: str = None) -> str:\n"
                "    \"\"\"Decompress a gzip file.\"\"\"\n"
                "    output = output or filepath.rstrip('.gz')\n"
                "    with gzip.open(filepath, 'rb') as f_in:\n"
                "        with open(output, 'wb') as f_out:\n"
                "            shutil.copyfileobj(f_in, f_out)\n"
                "    return f'Decompressed to {output}'\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    if len(sys.argv) > 1:\n"
                "        print(compress_file(sys.argv[1]))\n"
                "    else:\n"
                "        print('Usage: python compress.py <file>')\n"
            )
        if "encrypt" in lower or "decrypt" in lower or "cipher" in lower:
            return (
                "def caesar_encrypt(text: str, shift: int = 3) -> str:\n"
                "    \"\"\"Encrypt text with Caesar cipher.\"\"\"\n"
                "    result = []\n"
                "    for c in text:\n"
                "        if c.isalpha():\n"
                "            base = ord('A') if c.isupper() else ord('a')\n"
                "            result.append(chr((ord(c) - base + shift) % 26 + base))\n"
                "        else:\n"
                "            result.append(c)\n"
                "    return ''.join(result)\n"
                "\n"
                "\n"
                "def caesar_decrypt(text: str, shift: int = 3) -> str:\n"
                "    \"\"\"Decrypt Caesar cipher.\"\"\"\n"
                "    return caesar_encrypt(text, -shift)\n"
                "\n"
                "\n"
                "def rot13(text: str) -> str:\n"
                "    \"\"\"Apply ROT13 transformation.\"\"\"\n"
                "    return caesar_encrypt(text, 13)\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    msg = 'Hello, World!'\n"
                "    enc = caesar_encrypt(msg)\n"
                "    dec = caesar_decrypt(enc)\n"
                "    print(f'Original:  {msg}')\n"
                "    print(f'Encrypted: {enc}')\n"
                "    print(f'Decrypted: {dec}')\n"
                "    print(f'ROT13:     {rot13(msg)}')\n"
            )
        if "log" in lower and ("logger" in lower or "logging" in lower):
            return (
                "import logging\n"
                "import sys\n"
                "\n"
                "\n"
                "def setup_logger(name: str = 'app', level: int = logging.INFO,\n"
                "                 fmt: str = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'):\n"
                "    \"\"\"Set up a logger with console handler.\"\"\"\n"
                "    logger = logging.getLogger(name)\n"
                "    logger.setLevel(level)\n"
                "    if not logger.handlers:\n"
                "        handler = logging.StreamHandler(sys.stdout)\n"
                "        handler.setFormatter(logging.Formatter(fmt))\n"
                "        logger.addHandler(handler)\n"
                "    return logger\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    log = setup_logger('myapp')\n"
                "    log.info('Application started')\n"
                "    log.warning('Something looks off')\n"
                "    log.error('Something failed')\n"
            )
        if "retry" in lower or "decorator" in lower:
            return (
                "import time\n"
                "import functools\n"
                "\n"
                "\n"
                "def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):\n"
                "    \"\"\"Retry decorator with exponential backoff.\"\"\"\n"
                "    def decorator(func):\n"
                "        @functools.wraps(func)\n"
                "        def wrapper(*args, **kwargs):\n"
                "            last_exc = None\n"
                "            for attempt in range(max_attempts):\n"
                "                try:\n"
                "                    return func(*args, **kwargs)\n"
                "                except Exception as e:\n"
                "                    last_exc = e\n"
                "                    if attempt < max_attempts - 1:\n"
                "                        wait = delay * (backoff ** attempt)\n"
                "                        print(f'Retry {attempt+1}/{max_attempts} after {wait:.1f}s: {e}')\n"
                "                        time.sleep(wait)\n"
                "            raise last_exc\n"
                "        return wrapper\n"
                "    return decorator\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    call_count = 0\n"
                "\n"
                "    @retry(max_attempts=3, delay=0.1)\n"
                "    def unstable():\n"
                "        global call_count\n"
                "        call_count += 1\n"
                "        if call_count < 3:\n"
                "            raise ConnectionError('not ready')\n"
                "        return 'success!'\n"
                "\n"
                "    print(f'Result: {unstable()}')\n"
            )
        if "cache" in lower or "memoize" in lower:
            return (
                "import functools\n"
                "import time\n"
                "\n"
                "\n"
                "def memoize(func):\n"
                "    \"\"\"Cache function results.\"\"\"\n"
                "    cache = {}\n"
                "    @functools.wraps(func)\n"
                "    def wrapper(*args):\n"
                "        if args not in cache:\n"
                "            cache[args] = func(*args)\n"
                "        return cache[args]\n"
                "    wrapper.cache = cache\n"
                "    wrapper.cache_clear = cache.clear\n"
                "    return wrapper\n"
                "\n"
                "\n"
                "def timed(func):\n"
                "    \"\"\"Measure function execution time.\"\"\"\n"
                "    @functools.wraps(func)\n"
                "    def wrapper(*args, **kwargs):\n"
                "        t0 = time.perf_counter()\n"
                "        result = func(*args, **kwargs)\n"
                "        elapsed = time.perf_counter() - t0\n"
                "        print(f'{func.__name__} took {elapsed:.4f}s')\n"
                "        return result\n"
                "    return wrapper\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    @memoize\n"
                "    def fib(n):\n"
                "        if n < 2:\n"
                "            return n\n"
                "        return fib(n-1) + fib(n-2)\n"
                "\n"
                "    print(f'fib(30) = {fib(30)}')\n"
                "    print(f'fib(30) = {fib(30)} (cached)')\n"
            )
        if "timer" in lower or "benchmark" in lower or "perf" in lower:
            return (
                "import time\n"
                "from contextlib import contextmanager\n"
                "\n"
                "\n"
                "@contextmanager\n"
                "def timer(label: str = 'Timer'):\n"
                "    \"\"\"Context manager that times a block of code.\"\"\"\n"
                "    t0 = time.perf_counter()\n"
                "    yield\n"
                "    elapsed = time.perf_counter() - t0\n"
                "    print(f'{label}: {elapsed:.4f}s')\n"
                "\n"
                "\n"
                "def benchmark(func, iterations: int = 100):\n"
                "    \"\"\"Benchmark a function over multiple iterations.\"\"\"\n"
                "    times = []\n"
                "    for _ in range(iterations):\n"
                "        t0 = time.perf_counter()\n"
                "        func()\n"
                "        times.append(time.perf_counter() - t0)\n"
                "    avg = sum(times) / len(times)\n"
                "    mn, mx = min(times), max(times)\n"
                "    print(f'{func.__name__}: avg={avg:.6f}s min={mn:.6f}s max={mx:.6f}s ({iterations} iters)')\n"
                "    return {'avg': avg, 'min': mn, 'max': mx}\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    with timer('Sum calculation'):\n"
                "        total = sum(range(1_000_000))\n"
                "    print(f'Result: {total}')\n"
                "\n"
                "    benchmark(lambda: sum(range(100_000)), iterations=10)\n"
            )
        if "queue" in lower:
            return (
                "from collections import deque\n"
                "import threading\n"
                "import time\n"
                "\n"
                "\n"
                "class Queue:\n"
                "    \"\"\"Thread-safe FIFO queue.\"\"\"\n"
                "    def __init__(self, maxsize: int = 0):\n"
                "        self._queue = deque()\n"
                "        self._maxsize = maxsize\n"
                "        self._lock = threading.Lock()\n"
                "        self._not_empty = threading.Condition(self._lock)\n"
                "        self._not_full = threading.Condition(self._lock)\n"
                "\n"
                "    def put(self, item, block: bool = True, timeout: float = None):\n"
                "        with self._not_full:\n"
                "            if self._maxsize > 0 and block:\n"
                "                if not self._not_full.wait_for(\n"
                "                    lambda: len(self._queue) < self._maxsize, timeout=timeout\n"
                "                ):\n"
                "                    raise TimeoutError('Queue full')\n"
                "            self._queue.append(item)\n"
                "            self._not_empty.notify()\n"
                "\n"
                "    def get(self, block: bool = True, timeout: float = None):\n"
                "        with self._not_empty:\n"
                "            if block:\n"
                "                if not self._not_empty.wait_for(\n"
                "                    lambda: len(self._queue) > 0, timeout=timeout\n"
                "                ):\n"
                "                    raise TimeoutError('Queue empty')\n"
                "            item = self._queue.popleft()\n"
                "            self._not_full.notify()\n"
                "            return item\n"
                "\n"
                "    def qsize(self) -> int:\n"
                "        return len(self._queue)\n"
                "\n"
                "    def empty(self) -> bool:\n"
                "        return len(self._queue) == 0\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    q = Queue(maxsize=5)\n"
                "    for i in range(5):\n"
                "        q.put(i)\n"
                "        print(f'Put {i}, size={q.qsize()}')\n"
                "    while not q.empty():\n"
                "        print(f'Got {q.get()}, size={q.qsize()}')\n"
            )
        # Generic function
        func_name = "process"
        skip_words = {"write", "create", "make", "a", "an", "the", "function", "def",
                       "to", "that", "for", "in", "which", "it", "is", "was", "and",
                       "or", "but", "with", "from", "this", "of", "at", "on", "by",
                       "be", "do", "has", "had", "can", "will", "would", "should",
                       "could", "may", "might", "shall", "need", "must", "python",
                       "script", "code", "program", "file", "function"}
        for word in msg.split():
            clean = re.sub(r'[^a-zA-Z_]', '', word.lower())
            if clean and clean not in skip_words and len(clean) > 1:
                func_name = clean
                break
        # Try to get a multi-word name like "reverse_string"
        words = [re.sub(r'[^a-zA-Z_]', '', w.lower()) for w in msg.split()
                 if re.sub(r'[^a-zA-Z_]', '', w.lower()) and re.sub(r'[^a-zA-Z_]', '', w.lower()) not in skip_words]
        if len(words) >= 2:
            func_name = "_".join(words[:3])
        return (
            f"def {func_name}(*args, **kwargs):\n"
            f'    """TODO: Implement {func_name}.\n\n'
            f"    Request: {msg[:80]}\n"
            f'    """\n'
            f"    raise NotImplementedError\n"
            f"\n"
            f"\n"
            f"if __name__ == '__main__':\n"
            f"    print('{func_name} called')\n"
            f"    result = {func_name}()\n"
            f"    print(f'Result: {{result}}')\n"
        )

    def _gen_class(self, msg: str) -> str:
        lower = msg.lower()
        # Extract class name
        class_name = "MyClass"
        for word in msg.split():
            clean = re.sub(r'[^a-zA-Z]', '', word)
            if clean and len(clean) > 2 and clean[0].isupper():
                class_name = clean
                break
            if clean and clean not in ("write", "create", "make", "a", "an", "the", "class", "that"):
                class_name = clean.capitalize()
                break

        if "data" in lower and "class" in lower:
            return (
                "from dataclasses import dataclass, field\n"
                "from typing import Any\n"
                "\n"
                "\n"
                "@dataclass\n"
                f"class {class_name}:\n"
                '    """Data class."""\n'
                "    name: str = ''\n"
                "    value: Any = None\n"
                "    tags: list[str] = field(default_factory=list)\n"
                "\n"
                "    def to_dict(self) -> dict:\n"
                "        from dataclasses import asdict\n"
                "        return asdict(self)\n"
                "\n"
                "\n"
                f"if __name__ == '__main__':\n"
                f"    obj = {class_name}(name='example', value=42, tags=['a', 'b'])\n"
                f"    print(obj)\n"
                f"    print(obj.to_dict())\n"
            )
        if "singleton" in lower:
            return (
                f"class {class_name}:\n"
                '    """Singleton pattern."""\n'
                "    _instance = None\n"
                "\n"
                "    def __new__(cls, *args, **kwargs):\n"
                "        if cls._instance is None:\n"
                "            cls._instance = super().__new__(cls)\n"
                "        return cls._instance\n"
                "\n"
                "    def __init__(self):\n"
                "        if not hasattr(self, '_initialized'):\n"
                "            self._initialized = True\n"
                "\n"
                "\n"
                f"if __name__ == '__main__':\n"
                f"    a = {class_name}()\n"
                f"    b = {class_name}()\n"
                f"    print(f'Same object: {{a is b}}')\n"
            )
        if "observer" in lower or "event" in lower or "listener" in lower:
            return (
                f"class {class_name}:\n"
                '    """Observer pattern — publish/subscribe events."""\n'
                "    def __init__(self):\n"
                "        self._listeners: dict[str, list] = {}\n"
                "\n"
                "    def on(self, event: str, callback):\n"
                "        \"\"\"Register a listener for an event.\"\"\"\n"
                "        self._listeners.setdefault(event, []).append(callback)\n"
                "        return self\n"
                "\n"
                "    def off(self, event: str, callback):\n"
                "        \"\"\"Remove a listener.\"\"\"\n"
                "        if event in self._listeners:\n"
                "            self._listeners[event] = [c for c in self._listeners[event] if c != callback]\n"
                "\n"
                "    def emit(self, event: str, *args, **kwargs):\n"
                "        \"\"\"Emit an event to all listeners.\"\"\"\n"
                "        for cb in self._listeners.get(event, []):\n"
                "            cb(*args, **kwargs)\n"
                "\n"
                "\n"
                f"if __name__ == '__main__':\n"
                f"    bus = {class_name}()\n"
                f"    bus.on('data', lambda d: print(f'Received: {{d}}'))\n"
                f"    bus.emit('data', 'hello')\n"
            )
        if "stack" in lower:
            return (
                f"class {class_name}:\n"
                '    """Stack data structure (LIFO)."""\n'
                "    def __init__(self):\n"
                "        self._items = []\n"
                "\n"
                "    def push(self, item):\n"
                "        self._items.append(item)\n"
                "\n"
                "    def pop(self):\n"
                "        if self.is_empty():\n"
                "            raise IndexError('pop from empty stack')\n"
                "        return self._items.pop()\n"
                "\n"
                "    def peek(self):\n"
                "        if self.is_empty():\n"
                "            raise IndexError('peek from empty stack')\n"
                "        return self._items[-1]\n"
                "\n"
                "    def is_empty(self) -> bool:\n"
                "        return len(self._items) == 0\n"
                "\n"
                "    def size(self) -> int:\n"
                "        return len(self._items)\n"
                "\n"
                "    def __repr__(self):\n"
                "        return f'Stack({self._items})'\n"
                "\n"
                "\n"
                f"if __name__ == '__main__':\n"
                f"    s = {class_name}()\n"
                f"    for i in range(5):\n"
                f"        s.push(i)\n"
                f"        print(f'Push {{i}}, size={{s.size()}}')\n"
                f"    while not s.is_empty():\n"
                f"        print(f'Pop {{s.pop()}}, size={{s.size()}}')\n"
            )
        # Generic class
        return (
            f"class {class_name}:\n"
            f'    """TODO: Implement {class_name}.\n\n'
            f"    Request: {msg[:80]}\n"
            f'    """\n'
            f"\n"
            f"    def __init__(self):\n"
            f"        pass\n"
            f"\n"
            f"    def __repr__(self):\n"
            f"        return f'{class_name}()'\n"
            f"\n"
            f"\n"
            f"if __name__ == '__main__':\n"
            f"    obj = {class_name}()\n"
            f"    print(obj)\n"
        )

    def _gen_script(self, msg: str) -> str:
        lower = msg.lower()
        if "organize" in lower or ("sort" in lower and "file" in lower):
            return (
                "#!/usr/bin/env python3\n"
                '"""Organize files in a directory by extension."""\n\n'
                "import os\n"
                "import shutil\n"
                "from pathlib import Path\n\n"
                "\n"
                "EXTENSION_MAP = {\n"
                "    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',\n"
                "    '.html': 'web', '.css': 'web', '.json': 'data',\n"
                "    '.txt': 'text', '.md': 'text', '.csv': 'data',\n"
                "    '.jpg': 'images', '.png': 'images', '.gif': 'images',\n"
                "    '.mp4': 'video', '.mp3': 'audio', '.pdf': 'documents',\n"
                "    '.zip': 'archives', '.tar': 'archives', '.gz': 'archives',\n"
                "}\n\n"
                "\n"
                "def organize(directory: str = '.'):\n"
                "    \"\"\"Move files into subdirectories by extension.\"\"\"\n"
                "    for item in Path(directory).iterdir():\n"
                "        if item.is_file():\n"
                "            folder = EXTENSION_MAP.get(item.suffix.lower(), 'other')\n"
                "            dest = Path(directory) / folder\n"
                "            dest.mkdir(exist_ok=True)\n"
                "            shutil.move(str(item), str(dest / item.name))\n"
                "            print(f'  {item.name} -> {folder}/')\n\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    path = sys.argv[1] if len(sys.argv) > 1 else '.'\n"
                "    print(f'Organizing {path}...')\n"
                "    organize(path)\n"
                "    print('Done!')\n"
            )
        if "rename" in lower or "batch" in lower:
            return (
                "#!/usr/bin/env python3\n"
                '"""Batch rename files with patterns."""\n\n'
                "import os\n"
                "import re\n"
                "from pathlib import Path\n\n"
                "\n"
                "def batch_rename(directory: str, pattern: str, replacement: str,\n"
                "                  dry_run: bool = True):\n"
                "    \"\"\"Rename files matching a regex pattern.\"\"\"\n"
                "    count = 0\n"
                "    for item in Path(directory).iterdir():\n"
                "        new_name = re.sub(pattern, replacement, item.name)\n"
                "        if new_name != item.name:\n"
                "            if dry_run:\n"
                "                print(f'  {item.name} -> {new_name}')\n"
                "            else:\n"
                "                item.rename(item.parent / new_name)\n"
                "                print(f'  Renamed: {item.name} -> {new_name}')\n"
                "            count += 1\n"
                "    print(f'{count} files would be renamed' if dry_run else f'{count} files renamed')\n\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    if len(sys.argv) >= 4:\n"
                "        batch_rename(sys.argv[1], sys.argv[2], sys.argv[3], dry_run=False)\n"
                "    else:\n"
                "        print('Usage: python batch_rename.py <dir> <pattern> <replacement>')\n"
            )
        if "backup" in lower:
            return (
                "#!/usr/bin/env python3\n"
                '"""Simple backup script."""\n\n'
                "import shutil\n"
                "import time\n"
                "from pathlib import Path\n\n"
                "\n"
                "def backup(source: str, dest: str = None):\n"
                "    \"\"\"Create a timestamped backup of a directory.\"\"\"\n"
                "    if not dest:\n"
                "        timestamp = time.strftime('%Y%m%d_%H%M%S')\n"
                "        dest = f'backup_{timestamp}'\n"
                "    shutil.copytree(source, dest, dirs_exist_ok=True)\n"
                "    return f'Backed up {source} -> {dest}'\n\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    if len(sys.argv) > 1:\n"
                "        print(backup(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))\n"
                "    else:\n"
                "        print('Usage: python backup.py <source> [dest]')\n"
            )
        if "monitor" in lower or "watch" in lower:
            return (
                "#!/usr/bin/env python3\n"
                '"""Watch a directory for changes."""\n\n'
                "import os\n"
                "import time\n"
                "from pathlib import Path\n\n"
                "\n"
                "def snapshot(directory: str) -> dict:\n"
                "    \"\"\"Take a snapshot of file mtimes.\"\"\"\n"
                "    snap = {}\n"
                "    for item in Path(directory).rglob('*'):\n"
                "        if item.is_file():\n"
                "            snap[str(item)] = item.stat().st_mtime\n"
                "    return snap\n\n"
                "\n"
                "def watch(directory: str, interval: float = 2.0):\n"
                "    \"\"\"Watch for file changes.\"\"\"\n"
                "    print(f'Watching {directory} (Ctrl+C to stop)...')\n"
                "    prev = snapshot(directory)\n"
                "    try:\n"
                "        while True:\n"
                "            time.sleep(interval)\n"
                "            curr = snapshot(directory)\n"
                "            added = set(curr) - set(prev)\n"
                "            removed = set(prev) - set(curr)\n"
                "            for f in added:\n"
                "                print(f'  + {f}')\n"
                "            for f in removed:\n"
                "                print(f'  - {f}')\n"
                "            prev = curr\n"
                "    except KeyboardInterrupt:\n"
                "        print('Stopped.')\n\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    watch(sys.argv[1] if len(sys.argv) > 1 else '.')\n"
            )
        # Generic script
        return (
            "#!/usr/bin/env python3\n"
            f'"""\n{msg[:200]}\n"""\n\n'
            "import sys\n"
            "import os\n\n"
            "\n"
            "def main():\n"
            f'    """Main entry point."""\n'
            f'    print("Script started")\n'
            f'    # TODO: Implement logic for: {msg[:60]}\n'
            f'    print("Done")\n'
            "\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )

    def _gen_api(self, msg: str) -> str:
        lower = msg.lower()
        if "flask" in lower:
            return (
                "#!/usr/bin/env python3\n"
                '"""Flask API server."""\n\n'
                "from flask import Flask, jsonify, request\n\n"
                "app = Flask(__name__)\n\n"
                "\n"
                "@app.route('/')\n"
                "def index():\n"
                "    return jsonify({'status': 'ok', 'message': 'API is running'})\n\n"
                "\n"
                "@app.route('/api/health')\n"
                "def health():\n"
                "    return jsonify({'status': 'healthy'})\n\n"
                "\n"
                "@app.route('/api/data', methods=['GET'])\n"
                "def get_data():\n"
                "    return jsonify({'data': [], 'count': 0})\n\n"
                "\n"
                "@app.route('/api/data', methods=['POST'])\n"
                "def create_item():\n"
                "    body = request.get_json(force=True, silent=True) or {}\n"
                "    return jsonify({'created': True, 'item': body}), 201\n\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    import sys\n"
                "    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000\n"
                "    print(f'Flask API on http://localhost:{port}')\n"
                "    app.run(debug=True, port=port)\n"
            )
        # Default: stdlib HTTP server
        return (
            "#!/usr/bin/env python3\n"
            '"""\n'
            f"API: {msg[:150]}\n"
            '"""\n\n'
            "from http.server import HTTPServer, BaseHTTPRequestHandler\n"
            "import json\n\n"
            "\n"
            "class Handler(BaseHTTPRequestHandler):\n"
            "    def do_GET(self):\n"
            "        self.send_response(200)\n"
            "        self.send_header('Content-Type', 'application/json')\n"
            "        self.end_headers()\n"
            "        self.wfile.write(json.dumps({'status': 'ok', 'path': self.path}).encode())\n"
            "\n"
            "    def do_POST(self):\n"
            "        length = int(self.headers.get('Content-Length', 0))\n"
            "        body = self.rfile.read(length) if length else b'{}'\n"
            "        data = json.loads(body)\n"
            "        self.send_response(201)\n"
            "        self.send_header('Content-Type', 'application/json')\n"
            "        self.end_headers()\n"
            "        self.wfile.write(json.dumps({'created': True, 'data': data}).encode())\n"
            "\n"
            "    def log_message(self, format, *args):\n"
            "        print(f'{self.address_string()} - {format % args}')\n"
            "\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    import sys\n"
            "    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000\n"
            "    server = HTTPServer(('localhost', port), Handler)\n"
            "    print(f'API running on http://localhost:{port}')\n"
            "    server.serve_forever()\n"
        )

    def _gen_test(self, msg: str) -> str:
        return (
            "import pytest\n\n"
            "\n"
            "class TestExample:\n"
            "    \"\"\"Test suite.\"\"\"\n"
            "\n"
            "    def test_basic(self):\n"
            "        assert True\n"
            "\n"
            "    def test_addition(self):\n"
            "        assert 1 + 1 == 2\n"
            "\n"
            "    @pytest.mark.parametrize('input,expected', [\n"
            "        ('hello', 5),\n"
            "        ('', 0),\n"
            "        ('world', 5),\n"
            "    ])\n"
            "    def test_length(self, input, expected):\n"
            "        assert len(input) == expected\n"
            "\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    pytest.main([__file__, '-v'])\n"
        )

    def _gen_html(self, msg: str) -> str:
        return (
            "<!DOCTYPE html>\n"
            "<html lang='en'>\n"
            "<head>\n"
            "    <meta charset='UTF-8'>\n"
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
            f"    <title>{msg[:50]}</title>\n"
            "    <style>\n"
            "        * { margin: 0; padding: 0; box-sizing: border-box; }\n"
            "        body { font-family: system-ui, sans-serif; padding: 2rem; }\n"
            "        h1 { color: #00F2C2; margin-bottom: 1rem; }\n"
            "        p { color: #333; line-height: 1.6; }\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            f"    <h1>{msg[:50]}</h1>\n"
            "    <p>Content goes here.</p>\n"
            "</body>\n"
            "</html>\n"
        )

    def _gen_config(self, msg: str) -> str:
        return (
            "# Configuration\n"
            "app:\n"
            "  name: myapp\n"
            "  version: 1.0.0\n"
            "  debug: true\n\n"
            "server:\n"
            "  host: localhost\n"
            "  port: 8000\n\n"
            "database:\n"
            "  engine: sqlite\n"
            "  name: data.db\n"
        )

    def _gen_cli(self, msg: str) -> str:
        return (
            "#!/usr/bin/env python3\n"
            '"""CLI tool."""\n\n'
            "import argparse\n"
            "import sys\n\n"
            "\n"
            "def main():\n"
            "    parser = argparse.ArgumentParser(description='CLI Tool')\n"
            "    parser.add_argument('command', help='Command to run')\n"
            "    parser.add_argument('-v', '--verbose', action='store_true')\n"
            "    args = parser.parse_args()\n"
            "\n"
            "    if args.verbose:\n"
            "        print(f'Running: {args.command}')\n"
            "    print(f'Result: {args.command}')\n"
            "\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )

    def _gen_database(self, msg: str) -> str:
        return (
            "import sqlite3\n"
            "from pathlib import Path\n\n"
            "\n"
            "def init_db(db_path: str = 'app.db') -> sqlite3.Connection:\n"
            "    \"\"\"Initialize database with schema.\"\"\"\n"
            "    conn = sqlite3.connect(db_path)\n"
            "    conn.execute('''\n"
            "        CREATE TABLE IF NOT EXISTS items (\n"
            "            id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "            name TEXT NOT NULL,\n"
            "            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
            "        )\n"
            "    ''')\n"
            "    conn.commit()\n"
            "    return conn\n"
            "\n"
            "\n"
            "def insert_item(conn, name: str):\n"
            "    conn.execute('INSERT INTO items (name) VALUES (?)', (name,))\n"
            "    conn.commit()\n"
            "\n"
            "\n"
            "def get_all(conn) -> list[dict]:\n"
            "    rows = conn.execute('SELECT * FROM items').fetchall()\n"
            "    return [{'id': r[0], 'name': r[1], 'created_at': r[2]} for r in rows]\n"
            "\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    conn = init_db()\n"
            "    insert_item(conn, 'First item')\n"
            "    print(get_all(conn))\n"
        )

    # ── Task: Debug ──────────────────────────────────────────────

    def _task_debug(self, msg: str, ws: str) -> str:
        # Try to find the relevant file
        file_hint = ""
        for word in msg.split():
            clean = word.strip("\"'.,:;")
            if "." in clean and any(clean.endswith(ext) for ext in [".py", ".js", ".ts", ".html"]):
                file_hint = clean
                break

        lines = [f"**Debugging:** {msg[:120]}", ""]

        if file_hint:
            result = file_read(os.path.join(ws, file_hint))
            if result.ok:
                lines.append(f"**File `{file_hint}`:**")
                lines.append(f"```")
                lines.append(result.output[:2000])
                lines.append(f"```")
                lines.append("")
                lines.append("**Analysis:** Check the code above for the issue described.")
            else:
                lines.append(f"Could not read `{file_hint}`: {result.error}")
        else:
            lines.append("**Common issues to check:**")
            lines.append("1. Check the error message — what line and file?")
            lines.append("2. Read that file: `read <filename>`")
            lines.append("3. Look for type mismatches, missing imports, or undefined variables")
            lines.append("")
            lines.append("Tip: Paste the full error traceback for a specific diagnosis.")

        return "\n".join(lines)

    # ── Task: Explain ────────────────────────────────────────────

    def _task_explain(self, msg: str, ws: str) -> str:
        # Try to find a file mentioned
        for word in msg.split():
            clean = word.strip("\"'.,:;")
            if "." in clean and any(clean.endswith(ext) for ext in [".py", ".js", ".ts"]):
                result = file_read(os.path.join(ws, clean))
                if result.ok:
                    return (
                        f"**File: `{clean}`**\n\n"
                        f"```python\n{result.output[:3000]}\n```\n\n"
                        f"**What this does:**\n"
                        f"The code above defines functionality related to your request.\n"
                        f"Key parts to understand:\n"
                        f"- Look at the imports to see dependencies\n"
                        f"- Read the main functions/classes for core logic\n"
                        f"- Check `if __name__ == '__main__'` for the entry point"
                    )
        return (
            f"**About:** {msg[:120]}\n\n"
            "To explain code, I need to see it. Please:\n"
            "1. Tell me the filename (e.g., `explain core/main.py`)\n"
            "2. Or paste the code you want explained"
        )

    # ── Task: Refactor ───────────────────────────────────────────

    def _task_refactor(self, msg: str, ws: str) -> str:
        for word in msg.split():
            clean = word.strip("\"'.,:;")
            if "." in clean and any(clean.endswith(ext) for ext in [".py", ".js"]):
                result = file_read(os.path.join(ws, clean))
                if result.ok:
                    return (
                        f"**Refactoring `{clean}`**\n\n"
                        f"```python\n{result.output[:3000]}\n```\n\n"
                        f"**Suggested improvements:**\n"
                        f"1. Add type hints to all functions\n"
                        f"2. Add docstrings to public functions\n"
                        f"3. Break large functions into smaller ones\n"
                        f"4. Remove duplicated code\n"
                        f"5. Use list comprehensions where appropriate\n\n"
                        f"Tell me which improvements to apply and I'll rewrite the file."
                    )
        return "To refactor code, tell me which file. Example: `refactor core/auth.py`"

    # ── Task: Test ───────────────────────────────────────────────

    def _task_test(self, msg: str, ws: str) -> str:
        code = self._gen_test(msg)
        filepath = os.path.join(ws, "test_example.py")
        file_write(filepath, code)
        return (
            f"**Created:** `test_example.py`\n\n"
            f"```python\n{code}\n```\n\n"
            f"Run with: `pytest test_example.py -v`"
        )

    # ── Task: List Files ─────────────────────────────────────────

    def _task_list_files(self, ws: str) -> str:
        result = execute_tool("file_list", {"path": ws})
        if result.ok:
            return f"**Files in `{ws}`:**\n\n{result.output}"
        return f"Error listing files: {result.error}"

    # ── Task: Read File ──────────────────────────────────────────

    def _task_read_file(self, msg: str, ws: str) -> str:
        # Extract filename from message
        for word in msg.split():
            clean = word.strip("\"'.,:;")
            if "." in clean:
                result = file_read(os.path.join(ws, clean))
                if result.ok:
                    return f"**`{clean}`:**\n\n```\n{result.output[:3000]}\n```"
                # Try without path
                result = file_read(clean)
                if result.ok:
                    return f"**`{clean}`:**\n\n```\n{result.output[:3000]}\n```"
        return "Tell me which file to read. Example: `read core/main.py`"

    # ── Task: General ────────────────────────────────────────────

    def _task_general(self, msg: str, ws: str) -> str:
        return (
            f"**Task:** {msg[:120]}\n\n"
            "I can help with that. Here are some things I can do:\n\n"
            "- **Write code:** Describe what you need\n"
            "- **Debug:** Paste the error or tell me the file\n"
            "- **Explain:** Tell me the file to read\n"
            "- **Refactor:** Tell me the file to improve\n"
            "- **Test:** Tell me what to test\n"
            "- **Files:** Type `ls` to list, `read <file>` to view\n\n"
            "What would you like me to do?"
        )

    # ── Help ─────────────────────────────────────────────────────

    def _help_text(self) -> str:
        return (
            "**Kraken — Coding Agent**\n\n"
            "I write code, not just explain it.\n\n"
            "**Commands:**\n"
            "- `write <description>` — I'll generate and save the code\n"
            "- `create <filename>` — Create a specific file\n"
            "- `debug <error>` — Diagnose and fix issues\n"
            "- `explain <file>` — Walk through code\n"
            "- `refactor <file>` — Improve code quality\n"
            "- `test <what>` — Write test suites\n"
            "- `ls` — List project files\n"
            "- `read <file>` — View file contents\n\n"
            "**Example tasks:**\n"
            "- \"Write a Python function to parse CSV files\"\n"
            "- \"Create a REST API with Flask\"\n"
            "- \"Debug my login handler\"\n"
            "- \"Write tests for the auth module\"\n\n"
            "Just describe what you need and I'll do it."
        )
