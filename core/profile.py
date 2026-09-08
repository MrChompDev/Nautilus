"""Nautilus OS - Gamification System

Manages user profile, coins, XP, levels, achievements, and tool stats.
Storage: ~/.nautilus/profile.json
"""

import json
import math
from datetime import datetime
from pathlib import Path

PROFILE_DIR = Path.home() / ".nautilus"
PROFILE_PATH = PROFILE_DIR / "profile.json"

DEFAULT_PROFILE = {
    "version": 1,
    "username": "Crewmate",
    "xp": 0,
    "coins": 0,
    "achievements": [],
    "completed_tutorials": [],
    "tool_stats": {},
    "challenge_scores": {},
    "game_launches": {},
    "daily_streak": 0,
    "last_login": None,
    "created_at": None,
}

ACHIEVEMENTS = {
    # Recon
    "first_scan": {"name": "Reef Walker", "desc": "Run your first port scan", "xp": 25, "coins": 15},
    "full_outerve": {"name": "Deep Dive", "desc": "Complete all recon tools", "xp": 100, "coins": 50},
    "network_mapper": {"name": "Cartographer", "desc": "Map your entire local network", "xp": 50, "coins": 30},
    "dns_master": {"name": "DNS Whisperer", "desc": "Enumerate 10 DNS records", "xp": 50, "coins": 25},

    # Red Team
    "first_breach": {"name": "Hull Breach", "desc": "Complete your first red team challenge", "xp": 50, "coins": 30},
    "password_hunter": {"name": "Lock Picker", "desc": "Crack 10 passwords", "xp": 75, "coins": 40},
    "exploit_master": {"name": "Harpoon Smith", "desc": "Build 5 working exploits", "xp": 100, "coins": 60},

    # Blue Team
    "firewall_master": {"name": "Sea Wall", "desc": "Configure 5 firewall rules", "xp": 50, "coins": 30},
    "log_reader": {"name": "Wake Watcher", "desc": "Analyze 20 log entries", "xp": 50, "coins": 25},
    "incident_pro": {"name": "First Responder", "desc": "Complete 5 incident responses", "xp": 100, "coins": 50},

    # Forensics
    "memory_dredge": {"name": "Memory Dredger", "desc": "Extract 10 memory artifacts", "xp": 75, "coins": 40},
    "stegano_pro": {"name": "Message Finder", "desc": "Decode 5 steganographic messages", "xp": 75, "coins": 40},

    # Crypto
    "cipher_breaker": {"name": "Code Breaker", "desc": "Solve 10 cipher challenges", "xp": 50, "coins": 30},
    "rsa_scholar": {"name": "Key Master", "desc": "Complete all RSA challenges", "xp": 100, "coins": 50},

    # Tutorial
    "first_tutorial": {"name": "Eager Learner", "desc": "Complete your first tutorial", "xp": 25, "coins": 10},
    "all_tutorials": {"name": "Professor of the Deep", "desc": "Complete all tutorials", "xp": 200, "coins": 100},

    # Arcade
    "game_hopper": {"name": "Game Hopper", "desc": "Play 5 different games", "xp": 25, "coins": 25},
    "arcade_legend": {"name": "Arcade Legend", "desc": "Play all 24 games", "xp": 100, "coins": 100},

    # General
    "daily_streak_7": {"name": "Weekly Tide", "desc": "Log in 7 days in a row", "xp": 50, "coins": 30},
    "daily_streak_30": {"name": "Monthly Current", "desc": "Log in 30 days in a row", "xp": 200, "coins": 150},
    "level_5": {"name": "Rising Tide", "desc": "Reach level 5", "xp": 0, "coins": 50},
    "level_10": {"name": "Deep Current", "desc": "Reach level 10", "xp": 0, "coins": 100},
    "level_25": {"name": "Abyssal Commander", "desc": "Reach level 25", "xp": 0, "coins": 250},
    "coins_1000": {"name": "Treasure Hoard", "desc": "Earn 1000 coins total", "xp": 0, "coins": 50},
}


def _level_for_xp(xp: int) -> int:
    return int(math.sqrt(xp / 50))


def _xp_for_level(level: int) -> int:
    return int((level ** 2) * 50)


def _xp_to_next_level(xp: int) -> int:
    level = _level_for_xp(xp)
    return _xp_for_level(level + 1) - xp


class Profile:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if PROFILE_PATH.exists():
            try:
                with open(PROFILE_PATH) as f:
                    data = json.load(f)
                for key, val in DEFAULT_PROFILE.items():
                    if key not in data:
                        data[key] = val
                return data
            except (json.JSONDecodeError, OSError):
                pass
        data = DEFAULT_PROFILE.copy()
        data["created_at"] = datetime.now().isoformat()
        data["last_login"] = datetime.now().isoformat()
        self._save(data)
        return data

    def _save(self, data: dict = None):
        if data is None:
            data = self._data
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROFILE_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def check_daily_login(self):
        today = datetime.now().strftime("%Y-%m-%d")
        last = self._data.get("last_login", "")
        if last and last.startswith(today):
            return
        yesterday = datetime.now().replace(day=datetime.now().day - 1).strftime("%Y-%m-%d")
        if last and last.startswith(yesterday):
            self._data["daily_streak"] = self._data.get("daily_streak", 0) + 1
        else:
            self._data["daily_streak"] = 1
        self._data["last_login"] = datetime.now().isoformat()
        self.add_coins(10)
        self.add_xp(20)
        streak = self._data["daily_streak"]
        if streak >= 7:
            self.try_unlock("daily_streak_7")
        if streak >= 30:
            self.try_unlock("daily_streak_30")
        self._save()

    @property
    def username(self) -> str:
        return self._data["username"]

    @username.setter
    def username(self, value: str):
        self._data["username"] = value
        self._save()

    @property
    def coins(self) -> int:
        return self._data["coins"]

    @property
    def xp(self) -> int:
        return self._data["xp"]

    @property
    def level(self) -> int:
        return _level_for_xp(self._data["xp"])

    @property
    def xp_to_next(self) -> int:
        return _xp_to_next_level(self._data["xp"])

    @property
    def streak(self) -> int:
        return self._data.get("daily_streak", 0)

    @property
    def achievements(self) -> list[str]:
        return self._data["achievements"]

    @property
    def completed_tutorials(self) -> list[str]:
        return self._data["completed_tutorials"]

    def add_coins(self, amount: int):
        self._data["coins"] += amount
        self._save()

    def spend_coins(self, amount: int) -> bool:
        if self._data["coins"] >= amount:
            self._data["coins"] -= amount
            self._save()
            return True
        return False

    def add_xp(self, amount: int):
        old_level = self.level
        self._data["xp"] += amount
        new_level = self.level
        self._save()
        if new_level > old_level:
            for lvl in range(old_level + 1, new_level + 1):
                if lvl == 5:
                    self.try_unlock("level_5")
                elif lvl == 10:
                    self.try_unlock("level_10")
                elif lvl == 25:
                    self.try_unlock("level_25")

    def try_unlock(self, achievement_id: str) -> bool:
        if achievement_id in self._data["achievements"]:
            return False
        if achievement_id not in ACHIEVEMENTS:
            return False
        self._data["achievements"].append(achievement_id)
        ach = ACHIEVEMENTS[achievement_id]
        if ach["xp"] > 0:
            self._data["xp"] += ach["xp"]
        if ach["coins"] > 0:
            self._data["coins"] += ach["coins"]
        self._save()
        return True

    def complete_tutorial(self, tool_id: str) -> bool:
        if tool_id in self._data["completed_tutorials"]:
            return False
        self._data["completed_tutorials"].append(tool_id)
        self.add_xp(50)
        self.add_coins(25)
        self._save()
        if not self._data["completed_tutorials"]:
            pass
        if len(self._data["completed_tutorials"]) == 1:
            self.try_unlock("first_tutorial")
        return True

    def record_tool_use(self, tool_id: str):
        stats = self._data.setdefault("tool_stats", {})
        tool = stats.setdefault(tool_id, {"uses": 0, "best_score": None})
        tool["uses"] += 1
        self.add_xp(10)
        self.add_coins(5)
        self._save()

    def record_challenge(self, tool_id: str, score: int, stars: int):
        scores = self._data.setdefault("challenge_scores", {})
        existing = scores.get(tool_id, {})
        if score > existing.get("score", 0):
            scores[tool_id] = {"score": score, "stars": stars}
        coin_reward = 20 if stars <= 1 else 50 if stars <= 3 else 100
        xp_reward = 50 if stars <= 1 else 100 if stars <= 3 else 200
        self.add_coins(coin_reward)
        self.add_xp(xp_reward)
        self._save()

    def record_game_launch(self, game_id: str):
        launches = self._data.setdefault("game_launches", {})
        first_time = game_id not in launches
        launches[game_id] = launches.get(game_id, 0) + 1
        self.add_coins(5)
        if first_time:
            self.add_coins(10)
        played = len(launches)
        if played >= 5:
            self.try_unlock("game_hopper")
        if played >= 24:
            self.try_unlock("arcade_legend")
        self._save()

    def get_achievement_info(self, achievement_id: str) -> dict | None:
        return ACHIEVEMENTS.get(achievement_id)

    def get_all_achievements(self) -> list[dict]:
        result = []
        for aid, info in ACHIEVEMENTS.items():
            result.append({
                "id": aid,
                "name": info["name"],
                "desc": info["desc"],
                "unlocked": aid in self._data["achievements"],
            })
        return result

    def reset(self):
        self._data = DEFAULT_PROFILE.copy()
        self._data["created_at"] = datetime.now().isoformat()
        self._data["last_login"] = datetime.now().isoformat()
        self._save()
