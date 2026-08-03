from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
VERIFIED_SHORT_IDS = {
    "JN94JmHmfg0",
    "ZwFYqyY18FY",
    "aaJVpiTJzho",
    "J-9OxOWfh3U",
    "6vc000i2q7E",
    "tkswTMz9y6w",
}
CHANNEL_URL = "https://www.youtube.com/channel/UCK_sDfho_T_DFQy3WaJYAeg"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, {k: v or "" for k, v in attrs}))

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text.append(data.strip())


class YunaSiteContract(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.css = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.parser = PageParser()
        self.parser.feed(self.html)
        self.copy = " ".join(self.parser.text)

    def test_brand_promise_and_verified_identity_are_present(self) -> None:
        self.assertIn("YUNA", self.copy)
        self.assertIn("K-beauty, checked in Korea", self.copy)
        self.assertIn("@yuna-u7g", self.copy)
        self.assertIn(CHANNEL_URL, self.html)

    def test_verified_latest_shorts_are_linked(self) -> None:
        found = set(re.findall(r"youtube\.com/shorts/([A-Za-z0-9_-]{11})", self.html))
        self.assertEqual(found, VERIFIED_SHORT_IDS)

    def test_semantic_accessibility_contract(self) -> None:
        tags = [tag for tag, _ in self.parser.tags]
        for required in ("header", "nav", "main", "section", "footer"):
            self.assertIn(required, tags)
        self.assertEqual(tags.count("h1"), 1)
        self.assertIn('href="#main-content"', self.html)
        for tag, attrs in self.parser.tags:
            if tag == "img":
                self.assertTrue(attrs.get("alt"), attrs)
                self.assertTrue(attrs.get("width"), attrs)
                self.assertTrue(attrs.get("height"), attrs)

    def test_legal_and_tiktok_verification_assets_remain(self) -> None:
        for name in ("terms.html", "privacy.html", "tiktokynAqdcqwNc7ovScDOkwwlk1ipNs8CPB5.txt"):
            self.assertTrue((ROOT / name).is_file(), name)
        self.assertIn('href="terms.html"', self.html)
        self.assertIn('href="privacy.html"', self.html)
        self.assertIn("Creator API Lab", self.copy)
        self.assertIn("not affiliated with or endorsed by TikTok", self.copy)

    def test_all_local_links_resolve(self) -> None:
        for tag, attrs in self.parser.tags:
            if tag != "a":
                continue
            href = attrs.get("href", "")
            parsed = urlparse(href)
            if not href or href.startswith("#") or parsed.scheme or href.startswith("//"):
                continue
            target = ROOT / parsed.path
            self.assertTrue(target.exists(), href)

    def test_privacy_and_static_safety_boundary(self) -> None:
        self.assertNotRegex(self.html, r"<script\b")
        self.assertNotIn("google-analytics", self.html.lower())
        self.assertNotIn("googletagmanager", self.html.lower())
        self.assertNotRegex(self.html, r"\b(subscribers?|conversion rate|#1|best seller)\b")

    def test_local_channel_favicon_is_declared(self) -> None:
        self.assertIn('rel="icon"', self.html)
        self.assertIn('href="assets/yuna-channel-avatar.jpg"', self.html)
        self.assertTrue((ROOT / "assets" / "yuna-channel-avatar.jpg").is_file())

    def test_mobile_gallery_density_and_brand_touch_target(self) -> None:
        self.assertRegex(self.css, r"\.brand\s*\{[^}]*min-height:\s*44px")
        self.assertIn("@media (min-width: 361px) and (max-width: 720px)", self.css)
        self.assertRegex(
            self.css,
            r"@media \(min-width: 361px\) and \(max-width: 720px\)[\s\S]*?\.video-grid\s*\{[^}]*repeat\(2",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
