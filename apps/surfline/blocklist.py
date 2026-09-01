"""Ad and tracker blocklists for Surfline"""

# Known ad network domains (block requests to these)
AD_DOMAINS = {
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "google-analytics.com",
    "googletagmanager.com",
    "adservice.google.com",
    "ads.yahoo.com",
    "advertising.com",
    "adnxs.com",
    "adsrvr.org",
    "amazon-adsystem.com",
    "scorecardresearch.com",
    "taboola.com",
    "outbrain.com",
    "criteo.com",
    "quantserve.com",
    "adroll.com",
    "pubmatic.com",
    "rubiconproject.com",
}

# Known tracker domains
TRACKER_DOMAINS = {
    "facebook.net",
    "facebook.com/tr",
    "connect.facebook.net",
    "mc.yandex.ru",
    "www.googletagmanager.com",
    "static.hotjar.com",
    "analytics.twitter.com",
    "js.hs-analytics.com",
    "t.co",
    "px.ads.linkedin.com",
    "bat.bing.com",
}


def is_blocked(url: str) -> bool:
    """Return True if the URL points to an ad or tracker domain."""
    lowered = url.lower()
    for domain in AD_DOMAINS:
        if domain in lowered:
            return True
    for domain in TRACKER_DOMAINS:
        if domain in lowered:
            return True
    return False