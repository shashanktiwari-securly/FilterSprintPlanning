"""
Run the full sprint-analysis pipeline for one or more FILTER sprints.

For each sprint name passed on the command line (or the built-in default list)
this driver runs, in sequence:

    1. fetch_filter_sprint_meta.py   → product_FILTER/<slug>-sprint-data/sprint-meta.json
    2. fetch_filter_sprint_issues.py → product_FILTER/<slug>-sprint-data/issues.json
       (now scoped to FILTER + PTGM + FDSE)
    3. build_sprint_analysis.py      → "FILTER Sprint <Name> Analysis.xlsx"

Each step is a separate Python subprocess so failures bubble up clearly. If a
sprint fails, we record the error and keep going so partial progress survives.

Usage::

    python run_sprint_analyses.py
    python run_sprint_analyses.py sprint-Arthur sprint-Bertha
    python run_sprint_analyses.py --skip-fetch sprint-Hanna     # rebuild only
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEFAULT_SPRINTS = [
    "sprint-Arthur",
    "sprint-Bertha",
    "sprint-Cristobal",
    "sprint-Dolly",
    "sprint-Edouard",
    "sprint-Fay",
    "sprint-Gonzalo",
    "sprint-Hanna",
]


def run(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def fetch_meta(sprint_name: str) -> int:
    out = ROOT / "product_FILTER" / f"{sprint_name}-sprint-data" / "sprint-meta.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([
        sys.executable,
        str(ROOT / "fetch_filter_sprint_meta.py"),
        sprint_name,
        "--out",
        str(out),
    ])


def fetch_issues(sprint_name: str) -> int:
    return run([
        sys.executable,
        str(ROOT / "fetch_filter_sprint_issues.py"),
        sprint_name,
    ])


def build_workbook(sprint_name: str) -> int:
    return run([
        sys.executable,
        str(ROOT / "build_sprint_analysis.py"),
        sprint_name,
    ])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sprints", nargs="*", help="Sprint names (default: 6-sprint backlog)")
    ap.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip the Jira fetch steps and just rebuild from cached JSON",
    )
    args = ap.parse_args()
    sprints = args.sprints or DEFAULT_SPRINTS

    if not args.skip_fetch:
        for env_key in ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
            if not os.environ.get(env_key):
                raise SystemExit(f"Missing environment variable {env_key}")

    failures: list[tuple[str, str]] = []
    for s in sprints:
        print("\n" + "=" * 78)
        print(f"  {s}")
        print("=" * 78)
        if not args.skip_fetch:
            rc = fetch_meta(s)
            if rc != 0:
                failures.append((s, "fetch_filter_sprint_meta failed"))
                continue
            rc = fetch_issues(s)
            if rc != 0:
                failures.append((s, "fetch_filter_sprint_issues failed"))
                continue
        rc = build_workbook(s)
        if rc != 0:
            failures.append((s, "build_sprint_analysis failed"))

    print("\n" + "=" * 78)
    if failures:
        print(f"COMPLETED WITH {len(failures)} FAILURE(S):")
        for s, msg in failures:
            print(f"  {s}: {msg}")
        sys.exit(1)
    print(f"All {len(sprints)} sprint analyses completed successfully.")


if __name__ == "__main__":
    main()
