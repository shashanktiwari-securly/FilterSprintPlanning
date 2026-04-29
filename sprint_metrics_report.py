"""
Build sprint comparison report: Stories, Tasks, Subtasks, Defects, Escape Defects,
completion %, story points, velocity proxy, hours.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(
    r"C:\Users\Shashank\.cursor\projects\c-Users-Shashank-Documents-FilterSprintPlanning\agent-tools"
)

# Fresh Jira exports with timetracking + customfield_10005 (Story Points)
SPRINT_FILES = {
    "sprint-Arthur": [
        "a9b44834-f398-4c13-81c1-a774b1623898.txt",
        "c05a42f0-242b-4b68-a8fa-dcd6613b2007.txt",
    ],
    "sprint-Bertha": [
        "b36e46c0-11f3-4c13-a2d2-a9ca8fc3c0c0.txt",
        "d74d85dd-68ae-448e-8785-a9e4c94ac017.txt",
        "cc46e268-ae63-4e6c-9119-22b5f55e345f.txt",
    ],
    "sprint-Cristobal": [
        "5f26bb98-248c-4064-8ae7-96be365d0636.txt",
        "c00171ec-e11e-41c7-93a0-452b957e1490.txt",
    ],
    "sprint-Dolly": ["82ed5676-c1dc-424a-91f0-280c7f97a05c.txt"],
    "sprint-Edouard": [
        "260dc7e2-07ca-4042-901d-9bfbdb97b0aa.txt",
        "8788eb9d-7f56-41fd-9b42-81f865d1e1c3.txt",
        "3f638b0b-468c-47a6-96c7-297e831fda27.txt",
    ],
    "sprint-Fay": [
        "5c7e2170-e9f0-4e9a-85ee-6f952ff80436.txt",
        "fbc2d17b-fb7c-488e-8c00-95ec15108288.txt",
    ],
}

DEFECT_TYPES = {"Defect", "Bug (OLD - use Defect instead)"}
ST_POINTS = "customfield_10005"


def parse_issue(raw, sprint_name):
    f = raw["fields"]
    st = f.get("status") or {}
    cat = (st.get("statusCategory") or {}).get("key") or "unknown"
    it = f.get("issuetype") or {}
    is_sub = bool(it.get("subtask"))
    parent = f.get("parent")
    parent_key = parent.get("key") if parent else None
    sp = f.get(ST_POINTS)
    try:
        story_points = float(sp) if sp is not None else None
    except (TypeError, ValueError):
        story_points = None

    def sec(x):
        return int(x) if x is not None else 0

    return {
        "key": raw["key"],
        "sprint": sprint_name,
        "type": it.get("name", ""),
        "subtask": is_sub,
        "status": st.get("name", ""),
        "status_cat": cat,
        "done": cat == "done",
        "priority": (f.get("priority") or {}).get("name") or "",
        "assignee": (f.get("assignee") or {}).get("displayName") if f.get("assignee") else None,
        "parent_key": parent_key,
        "story_points": story_points,
        "timespent_sec": sec(f.get("timespent")),
        "aggregatetimespent_sec": sec(f.get("aggregatetimespent")),
        "timeoriginalestimate_sec": sec(f.get("timeoriginalestimate")),
        "aggregatetimeoriginalestimate_sec": sec(f.get("aggregatetimeoriginalestimate")),
    }


def bucket(row):
    t = row["type"]
    if t == "Story":
        return "Story"
    if t == "Task":
        return "Task"
    if t == "Escape Defect":
        return "Escape Defect"
    if t in DEFECT_TYPES:
        return "Defect"
    if row["subtask"]:
        return "Subtask (all types)"
    return "Other"


def load_all():
    by_sprint = {}
    for sp, files in SPRINT_FILES.items():
        rows = []
        for fn in files:
            path = BASE / fn
            if not path.exists():
                raise FileNotFoundError(path)
            with open(path, encoding="utf-8") as fp:
                data = json.load(fp)
            for issue in data.get("issues") or []:
                rows.append(parse_issue(issue, sp))
        by_sprint[sp] = rows
    return by_sprint


def pct(part, whole):
    return round(100 * part / whole, 1) if whole else 0.0


def main():
    by_sp = load_all()
    order = list(SPRINT_FILES.keys())
    per = {}

    for sp in order:
        rows = by_sp[sp]
        n = len(rows)
        buckets = defaultdict(list)
        for r in rows:
            buckets[bucket(r)].append(r)

        def done_count(rs):
            return sum(1 for x in rs if x["done"])

        bucket_summary = {}
        for bname, rs in buckets.items():
            bucket_summary[bname] = {
                "count": len(rs),
                "done": done_count(rs),
                "done_pct": pct(done_count(rs), len(rs)),
            }

        sp_total = sum(r["story_points"] or 0 for r in rows if r["story_points"])
        sp_done = sum(
            r["story_points"] or 0 for r in rows if r["done"] and r["story_points"]
        )
        sp_story = [r for r in rows if r["type"] == "Story"]
        sp_story_pts = sum(r["story_points"] or 0 for r in sp_story if r["story_points"])
        sp_story_done = sum(
            r["story_points"] or 0
            for r in sp_story
            if r["done"] and r["story_points"]
        )

        hours_direct = sum(r["timespent_sec"] for r in rows) / 3600.0
        hours_rollup_parents = (
            sum(r["aggregatetimespent_sec"] for r in rows if not r["subtask"]) / 3600.0
        )
        est_orig_direct = sum(r["timeoriginalestimate_sec"] for r in rows) / 3600.0
        est_rollup_parents = (
            sum(r["aggregatetimeoriginalestimate_sec"] for r in rows if not r["subtask"])
            / 3600.0
        )

        done_issues = sum(1 for r in rows if r["done"])
        unassigned = sum(1 for r in rows if not r["assignee"])

        per[sp] = {
            "total_issues": n,
            "overall_done_pct": pct(done_issues, n),
            "status_cat": {
                k: sum(1 for r in rows if r["status_cat"] == k) for k in ("done", "new", "indeterminate")
            },
            "buckets": bucket_summary,
            "story_points": {
                "sum_on_all_types": round(sp_total, 2),
                "sum_done_all_types": round(sp_done, 2),
                "completion_of_estimated_sp_pct": pct(sp_done, sp_total) if sp_total else None,
                "on_stories_only": round(sp_story_pts, 2),
                "on_stories_done": round(sp_story_done, 2),
                "stories_with_sp_populated": sum(
                    1 for r in sp_story if r["story_points"] is not None
                ),
            },
            "hours": {
                "sum_timespent_direct_h": round(hours_direct, 1),
                "sum_aggregatetimespent_non_subtask_h": round(hours_rollup_parents, 1),
                "sum_original_estimate_direct_h": round(est_orig_direct, 1),
                "sum_aggregate_original_estimate_non_subtask_h": round(est_rollup_parents, 1),
            },
            "unassigned_count": unassigned,
            "unassigned_pct": pct(unassigned, n),
        }

    # Averages across6 sprints (by sprint snapshot, not deduped keys)
    avg = {
        "avg_issues_per_sprint": round(
            sum(per[sp]["total_issues"] for sp in order) / len(order), 1
        ),
        "avg_overall_done_pct": round(
            sum(per[sp]["overall_done_pct"] for sp in order) / len(order), 1
        ),
        "avg_story_points_total": round(
            sum(per[sp]["story_points"]["sum_on_all_types"] for sp in order) / len(order), 2
        ),
        "avg_story_points_completed": round(
            sum(per[sp]["story_points"]["sum_done_all_types"] for sp in order) / len(order), 2
        ),
        "avg_hours_direct": round(
            sum(per[sp]["hours"]["sum_timespent_direct_h"] for sp in order) / len(order), 1
        ),
        "avg_hours_rollup_non_subtask": round(
            sum(per[sp]["hours"]["sum_aggregatetimespent_non_subtask_h"] for sp in order)
            / len(order),
            1,
        ),
    }

    # Velocity proxy: story points marked done (all types) per sprint
    velocity_sp = [per[sp]["story_points"]["sum_done_all_types"] for sp in order]

    out = {
        "sprints": per,
        "averages_across_sprints": avg,
        "velocity_story_points_done_per_sprint": {
            sp: per[sp]["story_points"]["sum_done_all_types"] for sp in order
        },
        "notes": [
            "Counts are per sprint board snapshot (issues can appear in multiple sprint names if carried over).",
            "Subtask bucket includes Dev, QA, Automation, Sub-task, etc.",
            "Hours: sum_timespent_direct_h sums only work logged on each issue (no double-count from hierarchy).",
            "Hours: sum_aggregatetimespent_non_subtask_h sums Jira rollup on parents only (includes child work once per tree).",
            "Story Points field: customfield_10005; may be null on many issue types.",
        ],
    }

    outp = Path(__file__).parent / "sprint_comparison_metrics.json"
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    # Markdown-friendly tables to stdout
    print("## Sprint comparison (product_FILTER / FILTER)\n")
    print(
        "| Sprint | Issues | Done % | SP total | SP done (velocity) | Hours (direct) | Hours (parent rollup) |"
    )
    print(
        "|--------|-------:|-------:|---------:|-------------------:|---------------:|----------------------:|"
    )
    for sp in order:
        p = per[sp]
        h = p["hours"]
        s = p["story_points"]
        print(
            f"| {sp} | {p['total_issues']} | {p['overall_done_pct']}% | "
            f"{s['sum_on_all_types']} | {s['sum_done_all_types']} | "
            f"{h['sum_timespent_direct_h']} | {h['sum_aggregatetimespent_non_subtask_h']} |"
        )

    print("\n### Averages (6 sprints)\n")
    for k, v in avg.items():
        print(f"- **{k}**: {v}")

    print("\n### Work mix + completion by bucket\n")
    all_buckets = set()
    for sp in order:
        all_buckets.update(per[sp]["buckets"].keys())
    for b in sorted(all_buckets):
        print(f"\n**{b}**")
        print("| Sprint | Count | Done | Done % |")
        print("|--------|------:|-----:|-------:|")
        for sp in order:
            bkt = per[sp]["buckets"].get(b, {"count": 0, "done": 0, "done_pct": 0})
            print(
                f"| {sp} | {bkt['count']} | {bkt['done']} | {bkt['done_pct']}% |"
            )

    print(f"\nJSON: {outp}")


if __name__ == "__main__":
    main()
