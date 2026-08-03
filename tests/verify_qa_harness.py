from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "qa_site.py"


class QAHarnessContract(unittest.TestCase):
    def test_uses_ephemeral_local_port_instead_of_fixed_port(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn('ThreadingHTTPServer(("127.0.0.1", 0)', source)
        self.assertNotIn('BASE = "http://127.0.0.1:8765/"', source)

    def test_forces_lazy_images_to_load_before_full_page_capture(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn("i.loading = 'eager'", source)
        self.assertIn("window.scrollTo(0, document.body.scrollHeight)", source)

    def test_ignores_only_expected_canceled_navigation_events(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn('params.get("canceled") and params.get("errorText") == "net::ERR_ABORTED"', source)

    def test_blurs_qa_focus_before_clean_capture(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn("document.activeElement?.blur()", source)

    def test_suppresses_expected_windows_connection_reset_noise(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn("class QuietThreadingHTTPServer(ThreadingHTTPServer):", source)
        self.assertIn("def handle_error", source)

    def test_waits_for_target_document_before_forcing_lazy_images(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn("def wait_ready(cdp: CDP, expected_url: str)", source)
        self.assertIn("location.href", source)
        self.assertIn("wait_ready(cdp, url)", source)

    def test_uses_ephemeral_cdp_port_owned_by_temp_profile(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn('"--remote-debugging-port=0"', source)
        self.assertIn('profile / "DevToolsActivePort"', source)
        self.assertIn("except (FileNotFoundError, PermissionError, ValueError):", source)
        self.assertNotIn("9341", source)
        self.assertNotRegex(source, r"PORT\s*=\s*\d+")

    def test_waits_after_forced_chrome_termination(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn("except subprocess.TimeoutExpired:", source)
        self.assertRegex(source, r"proc\.kill\(\)\s+proc\.wait\(timeout=5\)")

    def test_external_request_gate_ignores_browser_internal_data_urls(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn('urllib.parse.urlparse(u).scheme in {"http", "https"}', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
