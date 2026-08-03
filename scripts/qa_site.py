from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests
import websocket

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".qa"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass

    def copyfile(self, source, outputfile) -> None:
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:
        error = sys.exc_info()[1]
        if isinstance(error, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


class CDP:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=15, origin="http://localhost")
        self.next_id = 0
        self.events: list[dict] = []

    def call(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        ident = self.next_id
        self.ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == ident:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})
            self.events.append(message)

    def drain(self, seconds: float = 0.4) -> None:
        old_timeout = self.ws.gettimeout()
        self.ws.settimeout(0.05)
        end = time.time() + seconds
        try:
            while time.time() < end:
                try:
                    self.events.append(json.loads(self.ws.recv()))
                except Exception:
                    pass
        finally:
            self.ws.settimeout(old_timeout)

    def close(self) -> None:
        self.ws.close()


def eval_value(cdp: CDP, expression: str):
    result = cdp.call("Runtime.evaluate", {"expression": expression, "returnByValue": True})
    if "exceptionDetails" in result:
        raise RuntimeError(result["exceptionDetails"])
    return result["result"].get("value")


def wait_ready(cdp: CDP, expected_url: str) -> None:
    for _ in range(200):
        location = eval_value(cdp, "location.href")
        state = eval_value(cdp, "document.readyState")
        if location == expected_url and state in ("interactive", "complete"):
            break
        time.sleep(0.05)
    else:
        raise TimeoutError(f"target document did not commit: {expected_url}")

    eval_value(cdp, "Array.from(document.images).forEach(i => { i.loading = 'eager'; })")
    eval_value(cdp, "window.scrollTo(0, document.body.scrollHeight)")
    for _ in range(250):
        state = eval_value(cdp, "document.readyState")
        loaded = eval_value(cdp, "Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)")
        if state == "complete" and loaded:
            eval_value(cdp, "window.scrollTo(0, 0)")
            cdp.drain(0.25)
            return
        time.sleep(0.08)
    raise TimeoutError("document and images did not finish loading")


def capture_full(cdp: CDP, filename: str) -> Path:
    result = cdp.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True, "fromSurface": True})
    path = OUT / filename
    path.write_bytes(base64.b64decode(result["data"]))
    return path


OUT.mkdir(parents=True, exist_ok=True)
handler_factory = partial(QuietHandler, directory=str(ROOT))
server = QuietThreadingHTTPServer(("127.0.0.1", 0), handler_factory)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()
BASE = f"http://127.0.0.1:{server.server_port}/"
profile = Path(tempfile.mkdtemp(prefix="yuna-site-chrome-"))
proc = subprocess.Popen(
    [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--remote-allow-origins=*",
        "--remote-debugging-port=0",
        f"--user-data-dir={profile}",
        "about:blank",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
cdp: CDP | None = None

try:
    active_port_file = profile / "DevToolsActivePort"
    cdp_port = None
    for _ in range(100):
        try:
            active_port_lines = active_port_file.read_text(encoding="utf-8").splitlines()
            if active_port_lines:
                cdp_port = int(active_port_lines[0])
                break
        except (FileNotFoundError, PermissionError, ValueError):
            pass
        time.sleep(0.1)
    if cdp_port is None:
        raise RuntimeError("Chrome did not publish DevToolsActivePort")

    version = None
    for _ in range(100):
        try:
            version = requests.get(f"http://127.0.0.1:{cdp_port}/json/version", timeout=0.3).json()
            break
        except Exception:
            time.sleep(0.1)
    if not version:
        raise RuntimeError("Chrome CDP endpoint did not start")

    target = requests.put(
        f"http://127.0.0.1:{cdp_port}/json/new?{urllib.parse.quote(BASE, safe=':/?=&')}", timeout=5
    ).json()
    cdp = CDP(target["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Network.enable")

    cases = [
        ("home-desktop", BASE, 1440, 1000, False),
        ("home-tablet", BASE, 768, 1024, True),
        ("home-mobile", BASE, 390, 844, True),
        ("terms-desktop", BASE + "terms.html", 1280, 900, False),
        ("privacy-mobile", BASE + "privacy.html", 390, 844, True),
    ]
    results = []

    for name, url, width, height, mobile in cases:
        cdp.events.clear()
        cdp.call("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "mobile": mobile,
        })
        cdp.call("Page.navigate", {"url": url})
        wait_ready(cdp, url)
        qa = eval_value(cdp, r"""(() => {
          const root = document.documentElement;
          const body = document.body;
          const badImages = [...document.images]
            .filter(i => !i.complete || i.naturalWidth === 0)
            .map(i => i.getAttribute('src'));
          const emptyLinks = [...document.querySelectorAll('a')]
            .filter(a => !a.getAttribute('href'))
            .map(a => a.textContent.trim());
          const focusableTiny = [...document.querySelectorAll('a,button,input,select,textarea')]
            .map(el => { const r=el.getBoundingClientRect(); return {text:(el.textContent||'').trim().slice(0,40),w:r.width,h:r.height}; })
            .filter(x => x.w > 0 && x.h > 0 && x.h < 40);
          const headings = [...document.querySelectorAll('h1')].map(h => h.textContent.trim());
          return {
            title: document.title,
            url: location.href,
            viewport: [innerWidth, innerHeight],
            document: [root.scrollWidth, root.scrollHeight],
            body: [body.scrollWidth, body.scrollHeight],
            horizontalOverflow: root.scrollWidth - innerWidth,
            badImages,
            emptyLinks,
            focusableTiny,
            h1: headings,
            background: getComputedStyle(body).backgroundColor,
            stylesheetCount: document.styleSheets.length,
          };
        })()""")
        eval_value(cdp, "document.activeElement?.blur()")
        time.sleep(0.05)
        screenshot = capture_full(cdp, f"{name}.png")
        cdp.drain(0.25)

        runtime_errors = [
            e for e in cdp.events
            if e.get("method") == "Runtime.exceptionThrown"
            or (e.get("method") == "Runtime.consoleAPICalled" and e.get("params", {}).get("type") == "error")
        ]
        loading_failures = []
        for event in cdp.events:
            if event.get("method") != "Network.loadingFailed":
                continue
            params = event.get("params", {})
            if params.get("canceled") and params.get("errorText") == "net::ERR_ABORTED":
                continue
            loading_failures.append(event)
        bad_responses = [
            e.get("params", {}).get("response", {})
            for e in cdp.events
            if e.get("method") == "Network.responseReceived"
            and e.get("params", {}).get("response", {}).get("status", 200) >= 400
        ]
        requested = [
            e.get("params", {}).get("request", {}).get("url", "")
            for e in cdp.events if e.get("method") == "Network.requestWillBeSent"
        ]
        external = [u for u in requested if u and not u.startswith(BASE)]

        assert qa["horizontalOverflow"] <= 0, qa
        assert not qa["badImages"], qa
        assert not qa["emptyLinks"], qa
        assert qa["stylesheetCount"] >= 1, qa
        assert len(qa["h1"]) == 1, qa
        assert not runtime_errors, runtime_errors
        assert not loading_failures, loading_failures
        assert not bad_responses, bad_responses
        assert not external, external

        results.append({
            "case": name,
            "viewport": qa["viewport"],
            "document": qa["document"],
            "horizontal_overflow": qa["horizontalOverflow"],
            "images_ok": True,
            "runtime_errors": 0,
            "failed_requests": 0,
            "external_requests": 0,
            "focusable_under_40px": qa["focusableTiny"],
            "screenshot": str(screenshot),
        })

    print(json.dumps({
        "sentinel": "YUNA_KBEAUTY_SITE_BROWSER_QA_PASS",
        "chrome": version.get("Browser"),
        "cases": results,
    }, ensure_ascii=False, indent=2))
finally:
    if cdp is not None:
        try:
            cdp.close()
        except Exception:
            pass
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    server.shutdown()
    server.server_close()
    server_thread.join(timeout=5)
    shutil.rmtree(profile, ignore_errors=True)
