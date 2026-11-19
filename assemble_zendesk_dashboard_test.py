"""Status category counts must follow the Jira category key, not the translated name."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from assemble_zendesk_dashboard import load_issues


def _issue(key: str, category_key: str, category_name: str) -> dict:
    category = {"name": category_name}
    if category_key:
        category["key"] = category_key
    return {
        "key": key,
        "fields": {
            "project": {"key": "FILTER"},
            "created": "2026-08-10T12:00:00.000-0400",
            "summary": key,
            "status": {"name": category_name, "statusCategory": category},
            "issuetype": {"name": "Escape Defect"},
            "customfield_11201": 2,
        },
    }


class StatusCategoryTests(unittest.TestCase):
    def test_translated_done_counts_as_done(self) -> None:
        payload = {
            "issues": [
                _issue("FILTER-9", "done", "完成"),
                _issue("FILTER-10", "indeterminate", "进行中"),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "page.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            issues = load_issues([path])
        by_key = {issue["key"]: issue for issue in issues}
        self.assertTrue(by_key["FILTER-9"]["is_done"])
        self.assertEqual(by_key["FILTER-9"]["status_category"], "Done")
        self.assertFalse(by_key["FILTER-10"]["is_done"])
        self.assertEqual(by_key["FILTER-10"]["status_category"], "In Progress")

    def test_english_name_without_key_still_counts_as_done(self) -> None:
        payload = {"issues": [_issue("FILTER-11", "", "Done")]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "page.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            issues = load_issues([path])
        self.assertEqual(len(issues), 1)
        self.assertTrue(issues[0]["is_done"])
        self.assertEqual(issues[0]["status_category"], "Done")


if __name__ == "__main__":
    unittest.main()
