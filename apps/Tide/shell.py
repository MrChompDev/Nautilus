"""Tide internal shell — a pure-Python command interpreter.

Replaces the old behavior of spawning ``$SHELL -c`` / ``cmd.exe``. Everything
the shell needs (tokenizing, built-ins, pipelines, redirection, env/cwd state)
lives here in the stdlib, so Tide works with zero external shell binaries.

External *programs* are still executed directly via ``subprocess.Popen`` (no
``shell=True`` wrapper) so ``ls``, ``python3``, etc. behave as expected.
"""

from __future__ import annotations

import getpass
import os
import platform
import re
import shutil
import subprocess
import time


class ShellError(Exception):
    """Raised by built-ins to report a non-zero exit with a message."""


# ---------------------------------------------------------------------------
# Tokenizer & parser
# ---------------------------------------------------------------------------

def tokenize(line: str) -> list[tuple[str, str]]:
    """Split a command line into (kind, value) tokens.

    Recognizes quoted strings, escapes, and the operators
    ``;  |  &&  ||  <  >  >>``.
    """
    tokens: list[tuple[str, str]] = []
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in " \t":
            i += 1
            continue
        two = line[i : i + 2]
        if two in ("&&", "||", ">>"):
            tokens.append(("op", two))
            i += 2
            continue
        if c in ";|<>":
            tokens.append(("op", c))
            i += 1
            continue
        if c in "\"'":
            q = c
            i += 1
            word = ""
            while i < n and line[i] != q:
                if line[i] == "\\" and i + 1 < n:
                    word += line[i + 1]
                    i += 2
                else:
                    word += line[i]
                    i += 1
            if i < n:
                i += 1
            tokens.append(("word", word))
            continue
        word = ""
        while i < n:
            c = line[i]
            two = line[i : i + 2]
            if c in " \t;|<>" or two in ("&&", "||"):
                break
            if c in "\"'":
                q = c
                i += 1
                while i < n and line[i] != q:
                    word += line[i]
                    i += 1
                if i < n:
                    i += 1
                continue
            if c == "\\" and i + 1 < n:
                word += line[i + 1]
                i += 2
                continue
            word += c
            i += 1
        tokens.append(("word", word))
    return tokens


def split_logical(tokens: list[tuple[str, str]]) -> list[tuple[str, list]]:
    """Split tokens on ``;`` / ``&&`` / ``||`` into (separator, tokens) groups."""
    groups: list[tuple[str, list]] = []
    sep = ";"
    cur: list = []
    for kind, val in tokens:
        if kind == "op" and val in (";", "&&", "||"):
            groups.append((sep, cur))
            cur = []
            sep = val
        else:
            cur.append((kind, val))
    groups.append((sep, cur))
    return groups


def parse_group(group_tokens: list[tuple[str, str]]) -> list[dict]:
    """Split a logical group on ``|`` and parse each stage's argv/redirects."""
    stages: list[dict] = []
    cur = {"argv": [], "in": None, "out": None, "append": False}
    pending = None
    for kind, val in group_tokens:
        if kind == "word":
            if pending == "in":
                cur["in"] = val
                pending = None
            elif pending == "out":
                cur["out"] = val
                pending = None
            elif pending == "append":
                cur["append"] = True
                cur["out"] = val
                pending = None
            else:
                cur["argv"].append(val)
        else:
            if val == "<":
                pending = "in"
            elif val == ">":
                pending = "out"
            elif val == ">>":
                pending = "append"
            elif val == "|":
                stages.append(cur)
                cur = {"argv": [], "in": None, "out": None, "append": False}
    stages.append(cur)
    return stages


def expand(word: str, env: dict) -> str:
    """Expand ``~``, ``~name``, ``$VAR`` and ``${VAR}`` in a word."""
    home = env.get("HOME", os.path.expanduser("~"))
    if word == "~":
        return home
    if word.startswith("~/"):
        return os.path.join(home, word[2:])
    return re.sub(
        r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)",
        lambda m: env.get(m.group(1) or m.group(2) or "", ""),
        word,
    )


# ---------------------------------------------------------------------------
# Built-ins
# ---------------------------------------------------------------------------

def _b_pwd(s, argv, stdin):
    return s.cwd + "\n"


def _b_cd(s, argv, stdin):
    if len(argv) > 2:
        raise ShellError("cd: too many arguments") from None
    if len(argv) == 1:
        target = s.env.get("HOME") or os.path.expanduser("~")
    else:
        target = argv[1]
        if target == "-":
            target = s._prev_cwd or s.cwd
        elif not os.path.isabs(target):
            target = os.path.join(s.cwd, target)
    target = os.path.expanduser(os.path.normpath(target))
    if not os.path.isdir(target):
        raise ShellError(f"cd: no such directory: {argv[1] if len(argv) > 1 else ''}") from None
    s._prev_cwd = s.cwd
    s.cwd = target
    return ""


def _b_ls(s, argv, stdin):
    long_fmt = False
    all_f = False
    targets = []
    for a in argv[1:]:
        if a == "-a":
            all_f = True
        elif a in ("-l", "-la", "-al"):
            long_fmt = True
            all_f = all_f or "a" in a
        elif a.startswith("-") and all(c in "alh" for c in a[1:]):
            long_fmt = long_fmt or "l" in a
            all_f = all_f or "a" in a
        else:
            targets.append(a)
    if not targets:
        targets = ["."]
    lines = []
    for t in targets:
        path = t if os.path.isabs(t) else os.path.join(s.cwd, t)
        if len(targets) > 1:
            lines.append(f"{t}:\n")
        try:
            entries = sorted(os.listdir(path))
        except OSError as e:
            raise ShellError(f"ls: {t}: {e.strerror}") from None
        if not all_f:
            entries = [e for e in entries if not e.startswith(".")]
        for e in entries:
            full = os.path.join(path, e)
            if os.path.isdir(full) and not os.path.islink(full):
                display = e + "/"
            elif os.path.islink(full):
                display = e + "@"
            elif os.access(full, os.X_OK):
                display = e + "*"
            else:
                display = e
            if long_fmt:
                try:
                    st = os.stat(full)
                    mode = "d" if os.path.isdir(full) else "-"
                    lines.append(
                        f"{mode} {st.st_mode & 0o777:>04o} {st.st_size:>9} "
                        f"{time.strftime('%b %d %H:%M', time.localtime(st.st_mtime))} {display}\n"
                    )
                except OSError:
                    lines.append(f"{display}\n")
            else:
                lines.append(display + "  ")
        lines.append("\n")
    return "".join(lines)


def _b_echo(s, argv, stdin):
    return " ".join(argv[1:]) + "\n"


def _b_cat(s, argv, stdin):
    if len(argv) == 1:
        return stdin
    parts = []
    for p in argv[1:]:
        if p == "-":
            parts.append(stdin)
            continue
        try:
            with open(s.resolve(p), encoding="utf-8", errors="replace") as f:
                parts.append(f.read())
        except OSError as e:
            raise ShellError(f"cat: {p}: {e.strerror}") from None
    return "".join(parts)


def _b_mkdir(s, argv, stdin):
    parents = False
    paths = []
    for a in argv[1:]:
        if a == "-p":
            parents = True
        elif a.startswith("-"):
            raise ShellError(f"mkdir: unknown option: {a}") from None
        else:
            paths.append(a)
    if not paths:
        raise ShellError("mkdir: missing operand") from None
    for p in paths:
        target = p if os.path.isabs(p) else os.path.join(s.cwd, p)
        try:
            if parents:
                os.makedirs(target, exist_ok=True)
            else:
                os.mkdir(target)
        except OSError as e:
            raise ShellError(f"mkdir: {p}: {e.strerror}") from None
    return ""


def _b_rmdir(s, argv, stdin):
    if len(argv) < 2:
        raise ShellError("rmdir: missing operand") from None
    for p in argv[1:]:
        target = p if os.path.isabs(p) else os.path.join(s.cwd, p)
        try:
            os.rmdir(target)
        except OSError as e:
            raise ShellError(f"rmdir: {p}: {e.strerror}") from None
    return ""


def _b_rm(s, argv, stdin):
    recursive = False
    force = False
    paths = []
    for a in argv[1:]:
        if a in ("-r", "-rf", "-fr"):
            recursive = True
        elif a == "-f":
            force = True
        elif a.startswith("-"):
            raise ShellError(f"rm: unknown option: {a}") from None
        else:
            paths.append(a)
    if not paths:
        raise ShellError("rm: missing operand") from None
    for p in paths:
        target = p if os.path.isabs(p) else os.path.join(s.cwd, p)
        try:
            if os.path.isdir(target) and not os.path.islink(target):
                if recursive:
                    shutil.rmtree(target)
                elif force:
                    shutil.rmtree(target, ignore_errors=True)
                else:
                    raise ShellError(f"rm: cannot remove '{p}': Is a directory") from None
            else:
                os.remove(target)
        except OSError as e:
            raise ShellError(f"rm: {p}: {e.strerror}") from None
    return ""


def _b_cp(s, argv, stdin):
    recursive = False
    paths = []
    for a in argv[1:]:
        if a == "-r":
            recursive = True
        elif a.startswith("-"):
            raise ShellError(f"cp: unknown option: {a}") from None
        else:
            paths.append(a)
    if len(paths) < 2:
        raise ShellError("cp: missing destination") from None
    srcs, dst = paths[:-1], paths[-1]
    dst_full = dst if os.path.isabs(dst) else os.path.join(s.cwd, dst)
    for src in srcs:
        src_full = src if os.path.isabs(src) else os.path.join(s.cwd, src)
        try:
            if os.path.isdir(src_full):
                if not recursive:
                    raise ShellError(f"cp: omitting directory '{src}'") from None
                shutil.copytree(
                    src_full, os.path.join(dst_full, os.path.basename(src_full)),
                    dirs_exist_ok=True,
                )
            elif os.path.isdir(dst_full):
                shutil.copy2(src_full, os.path.join(dst_full, os.path.basename(src_full)))
            elif len(srcs) > 1:
                raise ShellError("cp: multiple sources to single destination") from None
            else:
                shutil.copy2(src_full, dst_full)
        except OSError as e:
            raise ShellError(f"cp: {src}: {e.strerror}") from None
    return ""


def _b_mv(s, argv, stdin):
    if len(argv) < 3:
        raise ShellError("mv: missing destination") from None
    srcs, dst = argv[1:-1], argv[-1]
    dst_full = dst if os.path.isabs(dst) else os.path.join(s.cwd, dst)
    for src in srcs:
        src_full = src if os.path.isabs(src) else os.path.join(s.cwd, src)
        try:
            if os.path.isdir(dst_full):
                shutil.move(src_full, os.path.join(dst_full, os.path.basename(src_full)))
            elif len(srcs) > 1:
                raise ShellError("mv: multiple sources to single destination") from None
            else:
                shutil.move(src_full, dst_full)
        except OSError as e:
            raise ShellError(f"mv: {src}: {e.strerror}") from None
    return ""


def _b_touch(s, argv, stdin):
    for p in argv[1:]:
        target = p if os.path.isabs(p) else os.path.join(s.cwd, p)
        try:
            with open(target, "a"):
                os.utime(target, None)
        except OSError as e:
            raise ShellError(f"touch: {p}: {e.strerror}") from None
    return ""


def _b_date(s, argv, stdin):
    return time.ctime() + "\n"


def _b_whoami(s, argv, stdin):
    name = s.env.get("USER") or s.env.get("USERNAME") or getpass.getuser()
    return (name or "user") + "\n"


def _b_uname(s, argv, stdin):
    return f"{platform.system()} {platform.release()}\n"


def _b_env(s, argv, stdin):
    return "".join(f"{k}={v}\n" for k, v in sorted(s.env.items()))


def _b_export(s, argv, stdin):
    if len(argv) == 1:
        return "".join(f"{k}={v}\n" for k, v in sorted(s.env.items()))
    out = []
    for a in argv[1:]:
        if "=" in a:
            k, v = a.split("=", 1)
            s.env[k] = v
        else:
            out.append(f"{a}={s.env.get(a, '')}")
    return "\n".join(out) + ("\n" if out else "")


def _b_history(s, argv, stdin):
    return "".join(f"{i:>4}  {c}\n" for i, c in enumerate(s.history, 1))


def _b_exit(s, argv, stdin):
    s._emit("", "exit")
    s._exit_requested = True
    return ""


def _b_clear(s, argv, stdin):
    s._emit("", "clear")
    return ""


def _b_false(s, argv, stdin):
    raise ShellError("") from None


def _b_help(s, argv, stdin):
    return (
        "Tide internal shell — no external shell required.\n\n"
        "  Built-ins: "
        + ", ".join(sorted(BUILTINS))
        + "\n\n"
        "  Pipelines ( | ), && / || / ; chains, redirection ( <, >, >> ),\n"
        "  $VAR and ~ expansion, command history (Up/Down), Ctrl+C abort.\n"
        "  Anything else is executed as a program found on your PATH.\n\n"
    )


def _b_harbor(s, argv, stdin):
    s._emit("  \u2693 Opening Harbor in current directory...\n", "accent")
    return ""


def _b_grep(s, argv, stdin):
    flags = re.MULTILINE
    numbered = False
    pattern = None
    files = []
    for a in argv[1:]:
        if a == "-i":
            flags |= re.IGNORECASE
        elif a == "-n":
            numbered = True
        elif a.startswith("-"):
            raise ShellError(f"grep: unknown option: {a}") from None
        elif pattern is None:
            pattern = a
        else:
            files.append(a)
    if pattern is None:
        raise ShellError("grep: no pattern given") from None
    rx = re.compile(pattern, flags)
    out = []
    if not files:
        for i, line in enumerate(stdin.splitlines()):
            if rx.search(line):
                out.append((f"{i + 1}:" if numbered else "") + line + "\n")
        return "".join(out)
    for f in files:
        try:
            with open(s.resolve(f), encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    line = line.rstrip("\n")
                    if rx.search(line):
                        prefix = f"{f}:" if len(files) > 1 else ""
                        out.append(prefix + (f"{i + 1}:" if numbered else "") + line + "\n")
        except OSError as e:
            raise ShellError(f"grep: {f}: {e.strerror}") from None
    return "".join(out)


def _b_head(s, argv, stdin):
    count = 10
    files = []
    idx = 1
    while idx < len(argv):
        a = argv[idx]
        if a == "-n":
            try:
                count = int(argv[idx + 1])
                idx += 2
            except (ValueError, IndexError):
                raise ShellError("head: invalid line count") from None
        elif a.startswith("-n"):
            try:
                count = int(a[2:])
            except ValueError:
                raise ShellError("head: invalid line count") from None
            idx += 1
        elif a.startswith("-"):
            raise ShellError(f"head: unknown option: {a}") from None
        else:
            files.append(a)
            idx += 1
    if not files:
        return "".join(stdin.splitlines()[:count]) + ("\n" if stdin else "")
    out = []
    for f in files:
        try:
            with open(s.resolve(f), encoding="utf-8", errors="replace") as fh:
                out.extend(fh.readlines()[:count])
        except OSError as e:
            raise ShellError(f"head: {f}: {e.strerror}") from None
    return "".join(out)


def _b_tail(s, argv, stdin):
    count = 10
    files = []
    idx = 1
    while idx < len(argv):
        a = argv[idx]
        if a == "-n":
            try:
                count = int(argv[idx + 1])
                idx += 2
            except (ValueError, IndexError):
                raise ShellError("tail: invalid line count") from None
        elif a.startswith("-n"):
            try:
                count = int(a[2:])
            except ValueError:
                raise ShellError("tail: invalid line count") from None
            idx += 1
        elif a.startswith("-"):
            raise ShellError(f"tail: unknown option: {a}") from None
        else:
            files.append(a)
            idx += 1
    if not files:
        lines = stdin.splitlines()
        return "".join(x + "\n" for x in lines[-count:])
    out = []
    for f in files:
        try:
            with open(s.resolve(f), encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
            out.extend(lines[-count:])
        except OSError as e:
            raise ShellError(f"tail: {f}: {e.strerror}") from None
    return "".join(out)


def _b_which(s, argv, stdin):
    found = []
    path = s.env.get("PATH", "")
    for name in argv[1:]:
        if os.path.sep in name:
            if os.path.isfile(name) and os.access(name, os.X_OK):
                found.append(os.path.abspath(name))
            continue
        for d in path.split(os.pathsep):
            if not d:
                continue
            cand = os.path.join(d, name)
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                found.append(cand)
                break
    return "".join(found) + ("\n" if found else "")


def _b_path(s, argv, stdin):
    return s.env.get("PATH", "") + "\n"


BUILTINS: dict[str, object] = {
    "pwd": _b_pwd, "cd": _b_cd, "ls": _b_ls,
    "ll": lambda s, a, i: _b_ls(s, ["ls", "-l"] + a[1:], i),
    "echo": _b_echo, "cat": _b_cat, "mkdir": _b_mkdir,
    "rmdir": _b_rmdir, "rm": _b_rm, "cp": _b_cp, "mv": _b_mv,
    "touch": _b_touch, "date": _b_date, "whoami": _b_whoami,
    "uname": _b_uname, "env": _b_env, "export": _b_export,
    "history": _b_history, "exit": _b_exit, "clear": _b_clear,
    "cls": _b_clear, "help": _b_help, "grep": _b_grep,
    "head": _b_head, "tail": _b_tail, "which": _b_which,
    "path": _b_path, "true": lambda s, a, i: "", "false": _b_false,
    "harbor": _b_harbor,
}


# ---------------------------------------------------------------------------
# InternalShell
# ---------------------------------------------------------------------------

class InternalShell:
    """Stateful pure-Python shell for a single terminal session."""

    def __init__(self, initial_cwd: str | None = None, env: dict | None = None):
        self.cwd = os.path.abspath(initial_cwd or os.getcwd())
        self.env = dict(os.environ if env is None else env)
        self.history: list[str] = []
        self._prev_cwd: str | None = None
        self._on_output = None
        self._exit_requested = False
        self._abort = False
        self._proc: subprocess.Popen | None = None

    # -- public API --------------------------------------------------------

    def execute(self, line: str, on_output=None) -> int:
        """Run one command line; returns the final exit code (0..255)."""
        self._on_output = on_output
        self._exit_requested = False
        self._abort = False
        line = line.strip()
        if not line:
            return 0
        self.history.append(line)
        tokens = tokenize(line)
        groups = split_logical(tokens)
        final_code = 0
        self._last_code = 0
        for sep, group_tokens in groups:
            if self._exit_requested:
                break
            if sep == "&&" and self._last_code != 0:
                continue
            if sep == "||" and self._last_code == 0:
                continue
            stages = parse_group(group_tokens)
            self._last_code = self._run_pipeline(stages)
            final_code = self._last_code
        self._on_output = None
        return final_code

    @property
    def exit_requested(self) -> bool:
        return self._exit_requested

    def request_abort(self) -> None:
        """Kill the currently running external process (Ctrl+C)."""
        self._abort = True
        if self._proc:
            try:
                self._proc.kill()
            except Exception:
                pass

    def resolve(self, path: str) -> str:
        """Resolve a possibly-relative path against the shell cwd."""
        if not path or os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.cwd, path))

    # -- pipeline execution ------------------------------------------------

    def _run_pipeline(self, stages: list[dict]) -> int:
        input_text: str | None = None
        if stages and stages[0]["in"]:
            in_path = stages[0]["in"]
            if not os.path.isabs(in_path):
                in_path = os.path.join(self.cwd, in_path)
            try:
                with open(in_path, encoding="utf-8", errors="replace") as f:
                    input_text = f.read()
            except OSError as e:
                self._emit(f"< {stages[0]['in']}: {e.strerror}\n", "err")
                return 1

        last = stages[-1]
        for idx, stage in enumerate(stages):
            argv = [expand(a, self.env) for a in stage["argv"]]
            if not argv:
                continue
            if idx == len(stages) - 1:
                if last["out"]:
                    text, code = self._materialize(stage, argv, input_text or "")
                    self._write_file(last["out"], text, last["append"])
                    return code
                if argv[0] not in BUILTINS and not self._exit_requested:
                    return self._stream_external(argv)
                text, code = self._materialize(stage, argv, input_text or "")
                self._emit(text, "err" if code else "out")
                return code
            text, code = self._materialize(stage, argv, input_text or "")
            input_text = text
        return 0

    def _materialize(self, stage: dict, argv: list[str], input_text: str):
        if argv[0] in BUILTINS:
            try:
                return BUILTINS[argv[0]](self, argv, input_text), 0
            except ShellError as e:
                return (str(e) + "\n" if str(e) else ""), 1
            except Exception as e:  # noqa: BLE001 - surface unexpected errors
                return f"{argv[0]}: {e}\n", 1
        return self._run_external(argv, input_text)

    def _run_external(self, argv: list[str], input_text: str | None):
        proc = self._spawn(argv, pipe_stdin=input_text is not None)
        if proc is None:
            self._emit(f"{argv[0]}: command not found\n", "err")
            return "", 127
        self._proc = proc
        try:
            out, _ = proc.communicate(input_text)
        finally:
            self._proc = None
        return out or "", proc.returncode

    def _stream_external(self, argv: list[str]) -> int:
        proc = self._spawn(argv, pipe_stdin=False)
        if proc is None:
            self._emit(f"{argv[0]}: command not found\n", "err")
            return 127
        self._proc = proc
        try:
            for line in proc.stdout:
                if self._abort:
                    proc.kill()
                    break
                self._emit(line, "out")
            proc.wait()
        finally:
            self._proc = None
        if proc.returncode != 0:
            self._emit(f"[exit code: {proc.returncode}]\n", "dim")
        return proc.returncode

    def _spawn(self, argv: list[str], pipe_stdin: bool) -> subprocess.Popen | None:
        stdin = subprocess.PIPE if pipe_stdin else subprocess.DEVNULL
        try:
            return subprocess.Popen(
                argv, cwd=self.cwd, env=self.env, stdin=stdin,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
        except FileNotFoundError:
            return None
        except OSError as e:
            self._emit(f"{argv[0]}: {e}\n", "err")
            return None

    def _write_file(self, path: str, text: str, append: bool) -> int:
        target = path if os.path.isabs(path) else os.path.join(self.cwd, path)
        mode = "a" if append else "w"
        try:
            with open(target, mode, encoding="utf-8") as f:
                f.write(text)
            return 0
        except OSError as e:
            self._emit(f">{path}: {e.strerror}\n", "err")
            return 1

    def _emit(self, text: str, style: str) -> None:
        if self._on_output and text:
            self._on_output(text, style)
