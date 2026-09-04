"""Custom search engine — scrapes Bing HTML results"""

import requests
import base64
from urllib.parse import quote, urlparse, parse_qs, unquote
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
}


def _decode_bing(link: str) -> str:
    """Decode a Bing redirect into the real URL."""
    if link.startswith("http") and "bing.com/ck" not in link:
        return link
    try:
        parsed = urlparse(link)
        qs = parse_qs(parsed.query)
        b64 = qs.get("u", [""])[0]
        if b64.startswith("a1"):
            b64 = b64[2:]
        padded = b64 + "=" * (-len(b64) % 4)
        return unquote(base64.b64decode(padded).decode("utf-8"))
    except Exception:
        return link


def search(query: str, max_results: int = 10) -> list[dict]:
    """Search Bing and return list of {title, url, snippet}."""
    url = "https://www.bing.com/search?q=" + quote(query)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for result in soup.select("li.b_algo")[:max_results]:
        title_tag = result.select_one("h2 a")
        snippet_tag = result.select_one(".b_caption p")
        if not title_tag:
            continue
        results.append({
            "title": title_tag.get_text(strip=True),
            "url": _decode_bing(title_tag.get("href", "")),
            "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
        })

    return results


def results_to_html(query: str, results: list[dict], colors: dict, fonts: dict) -> str:
    results_html = ""
    for r in results:
        results_html += f"""
        <div style="margin-bottom: 26px; font-family: '{fonts['ui']}';">
            <a href="{r['url']}" style="color: {colors['teal']}; text-decoration: none;
               font-size: 20px; line-height: 1.3;">{r['title']}</a>
            <div style="font-size: 13px; color: {colors['coral']}; margin: 2px 0;">{r['url'][:60]}</div>
            <div style="font-size: 14px; color: {colors['text']}; line-height: 1.58;">{r['snippet']}</div>
        </div>
        """

    if not results:
        results_html = f"""
        <div style="padding: 30px 0; color: {colors['text_muted']}; font-size: 16px;">
            No results found for "{query}".
        </div>
        """

    return f"""
    <html>
    <body style="background-color: {colors['bg_light']}; margin: 0; min-height: 100vh;">
        <!-- Top nav bar like Google -->
        <div style="background: {colors['bg_mid']}; padding: 14px 20px; border-bottom: 1px solid {colors['border']};
                    display: flex; align-items: center; gap: 20px;">
            <span style="color: {colors['coral']}; font-size: 24px; font-weight: bold;
                         font-family: '{fonts['ui']}';">Surfline</span>
            <div style="flex: 1; max-width: 620px; background: {colors['bg_dark']}; border-radius: 24px;
                        padding: 10px 18px; color: {colors['text_dark']}; font-family: '{fonts['ui']}';
                        border: 1px solid {colors['border']};">{query}</div>
        </div>
        <!-- Results below -->
        <div style="max-width: 650px; margin: 24px auto 0 120px; padding: 0 20px 60px;">
            {results_html}
        </div>
    </body>
    </html>
    """