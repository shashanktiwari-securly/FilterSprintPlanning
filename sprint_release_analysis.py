"""Sprint release completion % and unplanned Task highlights for product_FILTER."""
import json
from datetime import datetime
from pathlib import Path

BASE = Path(
    r"C:\Users\Shashank\.cursor\projects\c-Users-Shashank-Documents-FilterSprintPlanning\agent-tools"
)

SPRINT_FILES = {
    "sprint-Arthur": [
        "91afd244-23c0-473a-9783-be86a904d0b9.txt",
        "80748ffa-e6a8-4d54-b5a3-9f1fa626a256.txt",
    ],
    "sprint-Bertha": [
        "2c5952c6-4e42-40f4-b7e4-648567fe1cad.txt",
        "ddaf51fc-d9bb-43a3-a8e6-02f4e0fd23cf.txt",
        "8c07bd7f-7aca-4030-9fee-881448e4f668.txt",
    ],
    "sprint-Cristobal": [
        "928fa00a-26f3-49fd-a7f8-996e552fa51f.txt",
        "a52985dc-a189-4cf4-aa37-94c9bbb18877.txt",
    ],
    "sprint-Dolly": ["602e28fe-4551-498d-9d54-1e2749f44834.txt"],
    "sprint-Edouard": [
        "fada3f24-0292-4dda-8474-2cc0027c7b07.txt",
        "d452c339-8249-4aea-8d89-ec6a241043cd.txt",
        "1a5cead5-a02d-4016-81b1-3c5b2d703d67.txt",
    ],
    "sprint-Fay": [
        "a994fe3b-6059-4d94-ba17-126ce335072a.txt",
        "d70878ed-06e0-479e-b294-521591cb4595.txt",
    ],
    "sprint-Gonzalo": [
        "b536aab4-92f3-4ba6-a735-bb25d7b3af95.txt",
        "43b93244-4da0-4824-a516-8a9ee90cead8.txt",
        "b368da03-99c1-4701-94ee-6ed042500ee0.txt",
    ],
}


def parse_dt(s):
    if not s:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            return datetime.strptime(s.replace("Z", "+00:00"), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_sprint(name, files):
    rows = []
    for fn in files:
        with open(BASE / fn, encoding="utf-8") as fp:
            data = json.load(fp)
        for issue in data.get("issues") or []:
            f = issue["fields"]
            st = f.get("status") or {}
            cat = (st.get("statusCategory") or {}).get("key") or ""
            it = f.get("issuetype") or {}
            labels = f.get("labels") or []
            created = parse_dt(f.get("created"))
            parent = f.get("parent") or {}
            rows.append(
                {
                    "key": issue["key"],
                    "summary": (f.get("summary") or "")[:120],
                    "type": it.get("name", ""),
                    "subtask": bool(it.get("subtask")),
                    "status": st.get("name", ""),
                    "status_cat": cat,
                    "done": cat == "done",
                    "created": created,
                    "created_raw": f.get("created"),
                    "labels": labels,
                    "parent_key": parent.get("key"),
                }
            )
    return rows


def percentile_ts(timestamps, p):
    if not timestamps:
        return None
    xs = sorted(timestamps)
    idx = min(len(xs) - 1, int(round((p / 100.0) * (len(xs) - 1))))
    return xs[idx]


def analyze():
    order = list(SPRINT_FILES.keys())
    result = {"sprints": {}, "methodology": {}}

    all_release_pct = []
    all_task_done = []

    for sp in order:
        rows = load_sprint(sp, SPRINT_FILES[sp])
        n = len(rows)
        done_n = sum(1 for r in rows if r["done"])
        release_pct = round(100 * done_n / n, 1) if n else 0
        all_release_pct.append(release_pct)

        tasks = [r for r in rows if r["type"] == "Task"]
        t_done = sum(1 for r in tasks if r["done"])
        task_pct = round(100 * t_done / len(tasks), 1) if tasks else None
        if task_pct is not None:
            all_task_done.append(task_pct)

        all_created = [r["created"] for r in rows if r["created"]]
        p75_all = percentile_ts(all_created, 75)
        task_created = [r["created"] for r in tasks if r["created"]]
        p75_task = percentile_ts(task_created, 75)

        unplanned = []
        for r in tasks:
            lbl_hit = any("unplanned" in (x or "").lower() for x in r["labels"])
            late_all = p75_all and r["created"] and r["created"] >= p75_all
            late_task = p75_task and r["created"] and r["created"] >= p75_task
            if lbl_hit or late_all:
                unplanned.append(
                    {
                        "key": r["key"],
                        "summary": r["summary"],
                        "status": r["status"],
                        "done": r["done"],
                        "created": r["created_raw"][:10] if r["created_raw"] else "",
                        "reason": (["label:unplanned"] if lbl_hit else [])
                        + (
                            ["created>=p75(sprint scope)"]
                            if late_all and not lbl_hit
                            else []
                        ),
                    }
                )

        released_statuses = {
            "RELEASED TO PROD",
            "Release in Progress",
            "Released to Prod",
        }
        released_n = sum(1 for r in rows if r["status"] in released_statuses)

        result["sprints"][sp] = {
            "total_issues": n,
            "release_complete_pct_done_category": release_pct,
            "done_issues": done_n,
            "not_done_issues": n - done_n,
            "in_release_named_status_count": released_n,
            "tasks_total": len(tasks),
            "tasks_done": t_done,
            "tasks_done_pct": task_pct,
            "unplanned_tasks_highlighted": len(unplanned),
            "unplanned_tasks_pct_of_tasks": round(100 * len(unplanned) / len(tasks), 1)
            if tasks
            else 0,
            "unplanned_task_keys": unplanned,
        }

    result["averages"] = {
        "avg_release_complete_pct": round(
            sum(all_release_pct) / len(all_release_pct), 1
        ),
        "avg_task_done_pct": round(sum(all_task_done) / len(all_task_done), 1)
        if all_task_done
        else None,
    }
    result["methodology"] = {
        "release_complete": "Percent of issues whose Jira status category is `done` (green bucket: Done, Closed without action, etc.).",
        "unplanned_tasks": (
            "Task issues flagged if (a) any label contains 'unplanned' (case-insensitive), OR "
            "(b) issue `created` date is on/after the 75th percentile of `created` dates for ALL "
            "issues in the same sprint (proxy for mid-sprint scope adds). Not a substitute for "
            "Jira Sprint Report 'scope change' or sprint start dates."
        ),
    }

    out = Path(__file__).parent / "sprint_release_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    print("## Release % complete (done status category)\n")
    print("| Sprint | Issues | Done | **Release %** | Tasks | Tasks done % | Unplanned Tasks* |")
    print("|--------|-------:|-----:|--------------:|------:|-------------:|----------------:|")
    for sp in order:
        s = result["sprints"][sp]
        print(
            f"| {sp} | {s['total_issues']} | {s['done_issues']} | **{s['release_complete_pct_done_category']}%** | "
            f"{s['tasks_total']} | {s['tasks_done_pct'] or '—'}% | {s['unplanned_tasks_highlighted']} |"
        )

    print("\n*Unplanned Tasks = count of Tasks matching label 'unplanned' OR created in latest quartile of sprint scope (see methodology).\n")
    print("### Averages\n")
    print(f"- Average **release % complete**: **{result['averages']['avg_release_complete_pct']}%**")
    print(f"- Average **Task done %** (where Tasks exist): **{result['averages']['avg_task_done_pct']}%**\n")

    for sp in order:
        ut = result["sprints"][sp]["unplanned_task_keys"]
        if not ut:
            continue
        print(f"#### Highlighted Tasks — {sp} ({len(ut)})\n")
        for u in ut:
            print(
                f"- [{u['key']}](https://securly.atlassian.net/browse/{u['key']}) — {u['status']} — created {u['created']} — {', '.join(u['reason']) or 'late quartile'} — {u['summary'][:80]}..."
            )
        print()

    print(f"Full JSON: {out}")


if __name__ == "__main__":
    analyze()
