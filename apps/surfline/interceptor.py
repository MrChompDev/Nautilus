"""Request interceptor that blocks ads and trackers"""

from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

from apps.surfline.blocklist import is_blocked


class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.blocked_count = 0

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if is_blocked(url):
            self.blocked_count += 1
            info.block(True)