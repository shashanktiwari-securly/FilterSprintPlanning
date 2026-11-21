"""Live Jira refresh must not replace a good snapshot with an empty search."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import assemble_zendesk_dashboard as az


SAVED = {
    "title": "Monthly Escape Defect and Support Request Dashboard",
    "generated_at": "2026-08-31T13:59:07Z",
    "snapshot_date": "2026-08-31",
    "live": False,
    "created_issues": [
        {
            "key": "FILTER-1",
            "created": "2026-08-03T00:00:00+00:00",
            "project_key": "FILTER",
        }
    ],
    "kpis": {"created": 141},
}

RAW_ISSUE = {
    "key": "FILTER-99",
    "fields": {
        "summary": "example",
        "status": {"name": "Done", "statusCategory": {"name": "Done", "key": "done"}},
        "issuetype": {"name": "Escape Defect"},
        "priority": {"name": "P1"},
        "created": "2026-08-10T12:00:00.000+0000",
        "resolutiondate": "2026-08-11T12:00:00.000+0000",
        "statuscategorychangedate": "2026-08-11T12:00:00.000+0000",
        "project": {"key": "FILTER"},
        "assignee": {"displayName": "A"},
        "customfield_11201": 2,
    },
}

CREDS = {"JIRA_EMAIL": "person@example.com", "JIRA_API_TOKEN": "not-a-real-token"}


class LiveRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "dashboard.json"
        self.out.write_text(json.dumps(SAVED), encoding="utf-8")
        self.patches = [
            patch.object(az, "OUT", self.out),
            patch.dict(os.environ, CREDS),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(self.tmp.cleanup)
        for item in self.patches:
            self.addCleanup(item.stop)

    def test_empty_search_keeps_published_snapshot(self) -> None:
        with patch.object(az, "fetch_jira_search_pages", return_value=[]):
            result = az.live_dashboard()
        self.assertEqual(result["snapshot_date"], "2026-08-31")
        self.assertFalse(result["live"])
        self.assertEqual(result["kpis"]["created"], 141)
        self.assertEqual(result["created_issues"][0]["key"], "FILTER-1")
        self.assertEqual(json.loads(self.out.read_text(encoding="utf-8")), SAVED)

    def test_id_only_issues_do_not_wipe_snapshot(self) -> None:
        raw = [{"key": "FILTER-2", "fields": {}}]
        with patch.object(az, "fetch_jira_search_pages", return_value=raw):
            result = az.live_dashboard()
        self.assertEqual(result["kpis"]["created"], 141)
        self.assertEqual(result["snapshot_date"], "2026-08-31")

    def test_search_error_keeps_published_snapshot(self) -> None:
        with patch.object(
            az, "fetch_jira_search_pages", side_effect=RuntimeError("Jira HTTP 401")
        ):
            result = az.live_dashboard()
        self.assertEqual(result["snapshot_date"], "2026-08-31")
        self.assertEqual(len(result["created_issues"]), 1)

    def test_publish_refuses_to_rewrite_snapshot_when_search_is_empty(self) -> None:
        with patch.object(az, "fetch_jira_search_pages", return_value=[]):
            with self.assertRaises(RuntimeError) as caught:
                az.live_dashboard(require_live=True)
        self.assertIn("leaving the published snapshot unchanged", str(caught.exception))
        self.assertEqual(json.loads(self.out.read_text(encoding="utf-8"))["kpis"]["created"], 141)

    def test_successful_search_still_publishes_live_counts(self) -> None:
        with patch.object(az, "fetch_jira_search_pages", return_value=[RAW_ISSUE]):
            result = az.live_dashboard(require_live=True)
        today = datetime.now(timezone.utc).date().isoformat()
        self.assertTrue(result["live"])
        self.assertEqual(result["snapshot_date"], today)
        self.assertEqual(result["kpis"]["created"], 1)
        self.assertEqual(result["created_issues"][0]["key"], "FILTER-99")
        self.assertEqual(result["kpis"]["created_done"], 1)


if __name__ == "__main__":
    unittest.main()
