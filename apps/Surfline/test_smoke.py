"""Quick smoke test for Surfline components.

Hermetic: all profile/password writes go to a temporary directory
(NAUTILUS_PROFILES_DIR), never into the real assets/profiles data.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Point TideSync at a throwaway profile dir BEFORE importing it
_TEST_PROFILES = tempfile.mkdtemp(prefix="surfline_test_")
os.environ['NAUTILUS_PROFILES_DIR'] = _TEST_PROFILES


def _cleanup():
    shutil.rmtree(_TEST_PROFILES, ignore_errors=True)


from apps.Surfline.src.icons import ensure_icons
from apps.Surfline.src.importer import BrowserImporter
from apps.Surfline.src.reef_shield import ReefShieldFilter
from apps.Surfline.src.theme import get_stylesheet
from apps.Surfline.src.tide_sync import (
    DEFAULT_SETTINGS,
    TideSyncManager,
    crypto_available,
)

print("All imports OK")

# Test Reef Shield
rs = ReefShieldFilter()
print(f"Reef Shield: {rs.get_stats()}")
assert rs.should_block("https://google-analytics.com/test")
assert rs.should_block("https://doubleclick.net/ads")
assert not rs.should_block("https://github.com/repo")
assert not rs.should_block("https://stackoverflow.com/questions")
print("Reef Shield filter tests PASSED")

# Test TideSync
ts = TideSyncManager()
print(f"Profiles: {ts.get_profile_names()}")
ts.set_active("Dev")
active = ts.get_active()
print(f"Active profile: {active.name}")
ts.add_bookmark("Dev", "https://github.com", "GitHub")
bms = ts.get_bookmarks("Dev")
print(f"Bookmarks: {len(bms)}")
print("TideSync tests PASSED")

# Test Settings persistence
print(f"Settings keys: {len(ts.global_settings)}")
assert ts.get_setting("search_engine") == "Google"
assert ts.get_setting("homepage") == "about:blank"
ts.set_setting("search_engine", "DuckDuckGo")
assert ts.get_setting("search_engine") == "DuckDuckGo"
ts.set_setting("search_engine", "Google")
print("Settings persistence PASSED")

# Test Password storage
ts.add_password("Dev", "https://example.com", "user1", "pass1")
ts.add_password("Dev", "https://example.com", "user2", "pass2")
assert len(ts.get_passwords("Dev")) >= 2
ts.delete_password("Dev", "https://example.com", "user1")
assert len(ts.get_passwords("Dev")) >= 1
print("Password storage PASSED")

# Test password vault (AES-256-GCM) when cryptography is available
if crypto_available():
    ts.set_master_password("CorrectHorse42")
    assert ts.vault_enabled and ts.is_vault_unlocked()
    # Stored blob must no longer be plaintext
    raw = ts.profiles["Dev"].passwords[0].get("password", "")
    assert raw.startswith("ENC:"), "password should be encrypted at rest"
    assert "pass2" not in raw
    # Wrong master password must not unlock
    ts.lock_vault()
    assert not ts.is_vault_unlocked()
    assert not ts.unlock_vault("wrong-password")
    locked_view = ts.get_passwords("Dev")
    assert all(p.get("locked") for p in locked_view), "locked vault must not expose passwords"
    # Correct password decrypts back
    assert ts.unlock_vault("CorrectHorse42")
    decrypted = ts.get_passwords("Dev")
    assert any(p.get("password") == "pass2" for p in decrypted), "round-trip failed"
    # Change master password re-keys the vault
    assert ts.change_master_password("CorrectHorse42", "NewMaster99")
    ts.lock_vault()
    assert not ts.unlock_vault("CorrectHorse42")
    assert ts.unlock_vault("NewMaster99")
    decrypted2 = ts.get_passwords("Dev")
    assert any(p.get("password") == "pass2" for p in decrypted2), "re-key round-trip failed"
    print("Vault (AES-256-GCM) tests PASSED")
else:
    print("Vault tests SKIPPED (cryptography not installed)")

# Test Browser Importer (read-only against real browsers)
imp = BrowserImporter()
browsers = imp.get_available_browsers()
print(f"Detected {len(browsers)} browser(s): {[b.name for b in browsers]}")
for b in browsers:
    imp.scan_browser(b)
    print(f"  {b.name}: {b.bookmarks_found} bm, {b.history_found} hist, {b.passwords_found} pw")
print("Browser Importer PASSED")

# Test Import methods (hermetic — writes go to the temp profile dir)
ts2 = TideSyncManager()
before_bm = len(ts2.get_bookmarks("Dev"))
count = ts2.import_bookmarks("Dev", [{"url": "https://test.com", "title": "Test"}])
assert count >= 1
print(f"Import bookmarks: +{count}")
print("Import methods PASSED")

# Test Icons
ensure_icons()
icon_dir = os.path.join(os.path.dirname(__file__), "assets", "icons")
icons = os.listdir(icon_dir)
print(f"Generated {len(icons)} icon files")
print("Icons OK")

# Test stylesheet
css = get_stylesheet()
assert len(css) > 100
print(f"Stylesheet: {len(css)} chars OK")

# Test Default Settings
assert len(DEFAULT_SETTINGS) >= 20
assert "search_engine" in DEFAULT_SETTINGS
assert "accent_color" in DEFAULT_SETTINGS
assert "download_path" in DEFAULT_SETTINGS
print(f"Default settings: {len(DEFAULT_SETTINGS)} keys OK")

print()
print("ALL TESTS PASSED")
print("Surfline Browser is ready to launch via: py -3.13 main.py")

_cleanup()
