"""One-off analysis: sprint consistency across Jira export JSON files."""
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(
    r"C:\Users\Shashank\.cursor\projects\c-Users-Shashank-Documents-FilterSprintPlanning\agent-tools"
)

SPRINT_FILES = {
    "sprint-Arthur": [
        "c63b1fe2-72fc-4ed9-8667-d6f4e9505c58.txt",
        "d2a7d14c-f482-49c0-a396-8294f80a1a6a.txt",
    ],
    "sprint-Bertha": [
        "a650383a-967e-449c-886b-64172a56b847.txt",
        "ff6ff4b5-22a4-44df-9233-9723a5741730.txt",
        "5894e6f8-94ca-4a39-a709-0da53dddad86.txt",
    ],
    "sprint-Cristobal": [
        "c7afe288-6c30-4873-b147-6fa890643fa9.txt",
        "7a4326a9-a732-432f-81c8-205b9baff227.txt",
    ],
    "sprint-Dolly": ["707904c6-8240-4075-87e7-6b71101fcc2b.txt"],
    "sprint-Edouard": [
        "1c70d525-1d0d-4373-b299-b77918d35091.txt",
        "957a3599-4448-417e-9424-4882607a1001.txt",
        "1aad8019-510a-4455-899f-f10e2ace0f10.txt",
    ],
    "sprint-Fay": [
        "16f6da29-4252-4b1b-8efc-f69083826a6f.txt",
        "5f8fdce9-41f7-421a-a7f5-fc1a9af9b2f7.txt",
    ],
}

DEFECT_LIKE = {
    "Defect",
    "Escape Defect",
    "Bug (OLD - use Defect instead)",
}


def parse_issue(raw, sprint_name):
    f = raw["fields"]
    st = f.get("status") or {}
    cat = (st.get("statusCategory") or {}).get("key") or "unknown"
    it = f.get("issuetype") or {}
    asn = f.get("assignee") or {}
    parent = f.get("parent")
    parent_key = parent.get("key") if parent else None
    subtasks = f.get("subtasks") or []
    sub_types = []
    for st_ in subtasks:
        sf = st_.get("fields") or {}
        sit = (sf.get("issuetype") or {}).get("name")
        if sit:
            sub_types.append(sit)
    return {
        "key": raw["key"],
        "sprint": sprint_name,
        "summary": (f.get("summary") or "").strip(),
        "type": it.get("name", ""),
        "subtask": bool(it.get("subtask")),
        "status": st.get("name", ""),
        "status_cat": cat,
        "priority": (f.get("priority") or {}).get("name") or "",
        "assignee": asn.get("displayName") if asn else None,
        "parent_key": parent_key,
        "subtask_types": sub_types,
        "subtask_count": len(subtasks),
    }


def load_sprint(sprint_name, filenames):
    rows = []
    for fn in filenames:
        path = BASE / fn
        with open(path, encoding="utf-8") as fp:
            data = json.load(fp)
        for issue in data.get("issues") or []:
            rows.append(parse_issue(issue, sprint_name))
    return rows


def main():
    by_sprint = {}
    all_rows = []
    key_to_sprints = defaultdict(list)

    for sp, files in SPRINT_FILES.items():
        rows = load_sprint(sp, files)
        by_sprint[sp] = rows
        all_rows.extend(rows)
        for r in rows:
            key_to_sprints[r["key"]].append(sp)

    dup_keys = {k: v for k, v in key_to_sprints.items() if len(v) > 1}

    # Per-sprint metrics
    report = {"per_sprint": {}, "global": {}}

    sprint_order = list(SPRINT_FILES.keys())
    counts = {sp: len(by_sprint[sp]) for sp in sprint_order}

    # Issue type mix    all_types = sorted({r["type"] for r in all_rows})

    for sp in sprint_order:
        rows = by_sprint[sp]
        n = len(rows)
        tc = Counter(r["type"] for r in rows)
        sc = Counter(r["status_cat"] for r in rows)
        stnames = Counter(r["status"] for r in rows)
        pc = Counter(r["priority"] for r in rows)
        unassigned = sum(1 for r in rows if not r["assignee"])
        done_cat = sc.get("done", 0) / n if n else 0
        new_cat = sc.get("new", 0) / n if n else 0
        prog_cat = sc.get("indeterminate", 0) / n if n else 0

        report["per_sprint"][sp] = {
            "total": n,
            "type_counts": dict(tc.most_common()),
            "type_pct": {t: round(100 * tc[t] / n, 1) for t in sorted(tc.keys())},
            "status_category_pct": {
                k: round(100 * v / n, 1) for k, v in sc.items()
            },
            "priority_counts": dict(pc),
            "unassigned_count": unassigned,
            "unassigned_pct": round(100 * unassigned / n, 1) if n else 0,
            "done_category_pct": round(100 * done_cat, 1),
            "todo_category_pct": round(100 * new_cat, 1),
            "in_progress_category_pct": round(100 * prog_cat, 1),
            "distinct_statuses": len(stnames),
        }

    # Defect parents in sprint (non-subtask defect-like)
    def is_defect_parent(r):
        return (not r["subtask"]) and (r["type"] in DEFECT_LIKE)

    triangle_stats = {}
    for sp in sprint_order:
        defects = [r for r in by_sprint[sp] if is_defect_parent(r)]
        missing_dev = missing_qa = missing_auto = 0
        has_all = 0
        sub_counts = []
        for d in defects:
            typeset = set(d["subtask_types"])
            hd, hq, ha = "Dev" in typeset, "QA" in typeset, "Automation" in typeset
            if not hd:
                missing_dev += 1
            if not hq:
                missing_qa += 1
            if not ha:
                missing_auto += 1
            if hd and hq and ha:
                has_all += 1
            sub_counts.append(d["subtask_count"])
        nd = len(defects)
        triangle_stats[sp] = {
            "defect_parents": nd,
            "with_dev_qa_auto_subtasks": has_all,
            "pct_full_triangle": round(100 * has_all / nd, 1) if nd else None,
            "missing_dev_subtask": missing_dev,
            "missing_qa_subtask": missing_qa,
            "missing_automation_subtask": missing_auto,
            "avg_subtasks_per_defect": round(
                sum(sub_counts) / len(sub_counts), 2
            )
            if sub_counts
            else 0,
        }

    # Subtask summary prefix hints (Dev/QA/Automation subtasks only)
    prefix_stats = defaultdict(lambda: Counter())
    for r in all_rows:
        if not r["subtask"]:
            continue
        t = r["type"]
        if t not in ("Dev", "QA", "Automation"):
            continue
        s = r["summary"]
        if t == "Dev" and s.upper().startswith("DEV"):
            prefix_stats[r["sprint"]]["dev_ok"] += 1
        elif t == "Dev":
            prefix_stats[r["sprint"]]["dev_other"] += 1
        if t == "QA" and (s.upper().startswith("QA") or s.upper().startswith("QA-")):
            prefix_stats[r["sprint"]]["qa_ok"] += 1
        elif t == "QA":
            prefix_stats[r["sprint"]]["qa_other"] += 1
        if t == "Automation" and (
            "AUTO" in s[:12].upper() or s.upper().startswith("AUTOMATION")
        ):
            prefix_stats[r["sprint"]]["auto_ok"] += 1
        elif t == "Automation":
            prefix_stats[r["sprint"]]["auto_other"] += 1

    # Coefficient of variation for key type shares across sprints
    type_names = ["Dev", "QA", "Automation", "Defect", "Escape Defect", "Task", "Story"]
    cv = {}
    for t in type_names:
        pcts = [
            report["per_sprint"][sp]["type_pct"].get(t, 0) for sp in sprint_order
        ]
        mean = sum(pcts) / len(pcts)
        if mean < 0.5:
            cv[t] = None
        else:
            var = sum((x - mean) ** 2 for x in pcts) / len(pcts)
            cv[t] = round((var**0.5) / mean, 2) if mean else None

    report["global"] = {
        "total_issues": len(all_rows),
        "duplicate_keys_across_sprints": len(dup_keys),
        "sprint_totals": counts,
        "min_sprint": min(counts, key=counts.get),
        "max_sprint": max(counts, key=counts.get),
        "cv_issue_type_pct_across_sprints": cv,
        "defect_triangle": triangle_stats,
        "subtask_prefix_hints": {k: dict(v) for k, v in prefix_stats.items()},
    }

    out_path = Path(__file__).parent / "sprint_consistency_report.json"
    with open(out_path, "w", encoding="utf-8") as o:
        json.dump(report, o, indent=2)

    # Console summary
    print("=== Sprint sizes ===")
    for sp in sprint_order:
        print(f"  {sp}: {counts[sp]}")
    print(f" TOTAL unique rows: {len(all_rows)}")
    print(f"  Keys appearing in >1 sprint: {len(dup_keys)}")
    if dup_keys:
        for k, v in list(dup_keys.items())[:15]:
            print(f"    {k}: {v}")

    print("\n=== Done % (status category) ===")
    for sp in sprint_order:
        print(
            f"  {sp}: {report['per_sprint'][sp]['done_category_pct']}% done | "
            f"{report['per_sprint'][sp]['todo_category_pct']}% todo | "
            f"{report['per_sprint'][sp]['in_progress_category_pct']}% in-progress"
        )

    print("\n=== Unassigned % ===")
    for sp in sprint_order:
        print(f"  {sp}: {report['per_sprint'][sp]['unassigned_pct']}%")

    print("\n=== Issue type CV (lower = more consistent mix across sprints) ===")
    for t, val in cv.items():
        if val is not None:
            print(f"  {t}: CV={val}")

    print("\n=== Defect parent triangle (Dev+QA+Automation subtasks present) ===")
    for sp in sprint_order:
        ts = triangle_stats[sp]
        print(
            f"  {sp}: defects={ts['defect_parents']} | "
            f"full triangle={ts['with_dev_qa_auto_subtasks']} "
            f"({ts['pct_full_triangle']}%) | "
            f"avg subs/defect={ts['avg_subtasks_per_defect']}"
        )

    print(f"\nFull JSON: {out_path}")


if __name__ == "__main__":
    main()
