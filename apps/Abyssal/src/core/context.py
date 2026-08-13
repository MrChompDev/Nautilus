

class ContextKeyService:
    def __init__(self) -> None:
        self._keys: dict[str, bool] = {}
        self._listeners: dict[str, set] = {}

    def set(self, key: str, value: bool) -> None:
        old = self._keys.get(key, False)
        self._keys[key] = value
        if old != value and key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(value)
                except Exception:
                    pass

    def get(self, key: str) -> bool:
        return self._keys.get(key, False)

    def reset(self, key: str) -> None:
        self._keys.pop(key, None)

    def when(self, key: str, value: bool = True) -> bool:
        return self._keys.get(key, False) == value

    def match_rules(self, rules: str) -> bool:
        parts = rules.split("&&")
        for rule in parts:
            rule = rule.strip()
            if not rule:
                continue
            if "==" in rule:
                k, v = rule.split("==")
                v = v.strip().lower() == "true"
                if self._keys.get(k.strip(), False) != v:
                    return False
            elif "!" in rule:
                k = rule.replace("!", "").strip()
                if self._keys.get(k, False):
                    return False
            else:
                if not self._keys.get(rule.strip(), False):
                    return False
        return True

    def listen(self, key: str, callback) -> None:
        if key not in self._listeners:
            self._listeners[key] = set()
        self._listeners[key].add(callback)