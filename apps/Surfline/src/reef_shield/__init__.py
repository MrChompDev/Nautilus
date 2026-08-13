"""
Reef Shield - Network Request Filter Engine
Blocks ads and trackers using EasyList/Brave-style rules.
"""
import json
import os
import re


class ReefShieldFilter:
    def __init__(self):
        self.network_rules = []
        self.cosmetic_rules = []
        self.enabled = True
        self.block_count = 0
        self.data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "adblock"
        )
        os.makedirs(self.data_dir, exist_ok=True)
        self._load_builtin_rules()
        self._load_custom_rules()

    def _load_builtin_rules(self):
        """Load built-in blocking rules."""
        self.network_rules = [
            r"doubleclick\.net",
            r"googlesyndication\.com",
            r"googleadservices\.com",
            r"google-analytics\.com",
            r"googletagmanager\.com",
            r"googletagservices\.com",
            r"facebook\.com/tr",
            r"facebook\.net/en_US/fbevents",
            r"connect\.facebook\.net",
            r"analytics\.twitter\.com",
            r"ads-twitter\.com",
            r"ads\.facebook\.com",
            r"pixel\.adsafeprotected\.com",
            r"amazon-adsystem\.com",
            r"adnxs\.com",
            r"adsrvr\.org",
            r"adform\.net",
            r"demdex\.net",
            r"moatads\.com",
            r"taboola\.com",
            r"outbrain\.com",
            r"taboola\.com|outbrain\.com",
            r"pubmatic\.com",
            r"rubiconproject\.com",
            r"openx\.net",
            r"casalemedia\.com",
            r"turn\.com",
            r"media\.net",
            r"revcontent\.com",
            r"mgid\.com",
            r"criteo\.com",
            r"criteo\.net",
            r"bluekai\.com",
            r"bidswitch\.net",
            r"sharethrough\.com",
            r"spotxchange\.com",
            r"yieldmo\.com",
            r"simpli\.fi",
            r"indexww\.com",
            r"lijit\.com",
            r"prebid",
            r"/ads/",
            r"/ad/",
            r"/advert/",
            r"/banner/",
            r"\.ad\.",
            r"\.ads\.",
            r"\.advert\.",
            r"pagead2",
            r"popup.*ad",
            r"popunder",
            r"interstitial.*ad",
            r"\/track\/",
            r"\/pixel\/",
            r"pixel\.js",
            r"tracking\.js",
            r"beacon\.js",
        ]

        self.url_pattern_rules = []
        for rule in self.network_rules:
            try:
                self.url_pattern_rules.append(re.compile(rule, re.IGNORECASE))
            except re.error:
                pass

    def _load_custom_rules(self):
        custom_file = os.path.join(self.data_dir, "custom_rules.json")
        if os.path.exists(custom_file):
            try:
                with open(custom_file) as f:
                    data = json.load(f)
                for rule in data.get("blocked_domains", []):
                    try:
                        self.url_pattern_rules.append(re.compile(rule, re.IGNORECASE))
                    except re.error:
                        pass
            except (OSError, json.JSONDecodeError):
                pass

    def save_custom_rules(self, blocked_domains=None):
        custom_file = os.path.join(self.data_dir, "custom_rules.json")
        data = {"blocked_domains": blocked_domains or []}
        with open(custom_file, "w") as f:
            json.dump(data, f, indent=2)

    def should_block(self, url: str) -> bool:
        if not self.enabled:
            return False
        if not url:
            return False
        for pattern in self.url_pattern_rules:
            if pattern.search(url):
                self.block_count += 1
                return True
        return False

    def should_defuse_css(self, selector: str) -> bool:
        ad_css_selectors = [
            r"\.ad[s\-_]",
            r"\.advert",
            r"\.sponsor",
            r"\.promo",
            r"#ad[s\-_]",
            r"#advert",
            r"\.adsbygoogle",
            r"\.ad-slot",
            r"\.ad-container",
            r"\.ad-wrapper",
            r"data-ad",
            r"data-dfp",
            r"\.dfp-ad",
        ]
        for pattern in ad_css_selectors:
            if re.search(pattern, selector, re.IGNORECASE):
                return True
        return False

    def get_injection_css(self) -> str:
        return """
        .adsbygoogle, .ad-slot, .ad-container, .ad-wrapper,
        .sponsored-content, .promo-unit, .ad-unit,
        [id*="google_ads"], [id*="dfp-ad"],
        [class*="ad-wrapper"], [class*="ad-slot"],
        [data-ad-unit], [data-dfp-url] {
            display: none !important;
            height: 0 !important;
            width: 0 !important;
            visibility: hidden !important;
        }
        """

    def get_stats(self):
        return {
            "enabled": self.enabled,
            "total_blocked": self.block_count,
            "rule_count": len(self.url_pattern_rules),
        }

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


class ReefShieldUrlRequestInterceptor:
    def __init__(self, filter_engine: ReefShieldFilter):
        self.filter_engine = filter_engine
        self.blocked_requests = []

    def intercept_request(self, request_url: str, request_type: str) -> dict:
        """
        Returns action dict for WebEngineUrlRequestInterceptor.
        """
        if self.filter_engine.should_block(request_url):
            self.blocked_requests.append({
                "url": request_url,
                "type": request_type,
            })
            return {"action": "block"}
        return {"action": "allow"}

    def get_blocked_count(self):
        return len(self.blocked_requests)
