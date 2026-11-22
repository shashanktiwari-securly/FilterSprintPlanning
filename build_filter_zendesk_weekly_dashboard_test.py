"""Ticket text must stay text: it cannot close the page script or run as HTML."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import build_filter_zendesk_weekly_dashboard as dash


ROOT = Path(__file__).resolve().parent
PAYLOAD = "</script><img src=x onerror=\"alert(1)\">"


class DashboardHtmlTests(unittest.TestCase):
    def test_ticket_markup_stays_inside_the_script_payload(self) -> None:
        data = json.loads((ROOT / "reports" / "filter-zendesk-weekly-dashboard.json").read_text())
        issue = dict(data["created_issues"][0])
        issue["summary"] = PAYLOAD
        issue["assignee"] = "<svg onload=alert(1)>"
        issue["status"] = "In Progress <script>"
        data["created_issues"] = [issue]
        data["headline"] = PAYLOAD

        html = dash.write_html(data)

        self.assertNotIn(PAYLOAD, html)
        self.assertIn('\\u003c/script>\\u003cimg src=x onerror=\\"alert(1)\\">', html)
        self.assertIn("function escHtml(s)", html)
        self.assertIn("${escHtml(i.summary)}", html)
        self.assertIn("${escHtml(DATA.headline || '')}", html)


if __name__ == "__main__":
    unittest.main()
