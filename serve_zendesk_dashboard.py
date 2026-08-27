"""Serve the dashboard and refresh numbers from Jira on each /api/live request.

Env: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN

Usage::

    python3 serve_zendesk_dashboard.py
    # open http://127.0.0.1:8766/
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from assemble_zendesk_dashboard import live_dashboard

ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "docs" / "index.html"
HOST = "127.0.0.1"
PORT = 8766


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} {fmt % args}")

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/api/live", "/api/live.json"}:
            try:
                data = live_dashboard()
                self._send(200, json.dumps(data).encode("utf-8"), "application/json")
            except Exception as exc:
                payload = {"error": str(exc), "live": False}
                self._send(500, json.dumps(payload).encode("utf-8"), "application/json")
            return
        if path in {"/", "/index.html", "/docs/", "/docs/index.html"}:
            html = HTML_PATH.read_text(encoding="utf-8")
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/live.json":
            live = ROOT / "docs" / "live.json"
            if live.exists():
                self._send(200, live.read_bytes(), "application/json")
                return
        self._send(404, b"not found", "text/plain")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Live dashboard: http://{HOST}:{PORT}/  (Ctrl+C to stop)")
    print("Each page load calls /api/live and re-queries Jira when credentials are set.")
    server.serve_forever()


if __name__ == "__main__":
    main()
