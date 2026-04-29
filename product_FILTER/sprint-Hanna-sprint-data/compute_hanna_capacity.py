"""Compute per-person leave weekdays overlapping sprint-Hanna for FILTER India core team.

Sprint boundaries default from ``sprint-meta.json`` (run ``fetch_filter_sprint_meta.py``).
Fallback dates apply only if that file is missing."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
SPRINT_META_FILE = DATA_DIR / "sprint-meta.json"

_FALLBACK_START = date(2026, 4, 28)
_FALLBACK_END = date(2026, 5, 11)

COMPANY_HOLIDAYS: dict[date, str] = {
    date(2026, 1, 1): "New Year's Eve",
    date(2026, 1, 26): "Republic Day",
    date(2026, 2, 16): "Securly Wellness Day",
    date(2026, 3, 4): "Holi",
    date(2026, 3, 19): "Gudi Padwa",
    date(2026, 5, 1): "Maharashtra Day",
    date(2026, 5, 22): "Securly Wellness Day",
    date(2026, 7, 2): "Securly Wellness Day",
    date(2026, 7, 3): "Securly Wellness Day",
    date(2026, 9, 14): "Ganesh Chaturthi",
    date(2026, 10, 20): "Dusshera",
    date(2026, 11, 10): "Diwali Padwa",
    date(2026, 11, 11): "Bhai Dhooj",
}


def company_holidays_in_sprint(
    sprint_start: date | None = None,
    sprint_end: date | None = None,
) -> list[tuple[date, str]]:
    if sprint_start is None or sprint_end is None:
        sprint_start, sprint_end, _ = load_sprint_window()
    return sorted(
        (d, name)
        for d, name in COMPANY_HOLIDAYS.items()
        if sprint_start <= d <= sprint_end and d.weekday() < 5
    )


def effective_working_days(
    sprint_start: date | None = None,
    sprint_end: date | None = None,
    sprint_wd: int | None = None,
) -> int:
    if sprint_start is None or sprint_end is None or sprint_wd is None:
        sprint_start, sprint_end, sprint_wd = load_sprint_window()
    return max(0, sprint_wd - len(company_holidays_in_sprint(sprint_start, sprint_end)))


def load_sprint_window(meta_path: Path | None = None) -> tuple[date, date, int]:
    path = meta_path or SPRINT_META_FILE
    if path.is_file():
        m = json.loads(path.read_text(encoding="utf-8"))
        start = date.fromisoformat(m["start_date"])
        end = date.fromisoformat(m["end_date"])
        wd = int(m["working_days"])
        return start, end, wd
    count = 0
    d = _FALLBACK_START
    while d <= _FALLBACK_END:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    return _FALLBACK_START, _FALLBACK_END, count

# (submitted_prefix, status, start_dd_mm_yyyy, end_dd_mm_yyyy)
RAW_LEAVES: list[tuple[str, str, str, str]] = [
    ("harsh.vern", "Pending", "02-01-2026", "02-01-2026"),
    ("ashish@se", "Approved", "02-01-2026", "09-01-2026"),
    ("harsh.vern", "Pending", "22-01-2026", "27-01-2026"),
    ("surabhi.ch", "Pending", "26-02-2026", "27-02-2026"),
    ("shailendra", "Approved", "06-01-2026", "06-01-2026"),
    ("harsh.vern", "Pending", "23-01-2026", "23-01-2026"),
    ("altamash@", "Pending", "01-04-2026", "01-04-2026"),
    ("shailendra", "Approved", "30-03-2026", "30-03-2026"),
    ("vaibhav.ku", "Pending", "27-04-2026", "15-05-2026"),
    ("ashish@se", "Pending", "02-04-2026", "02-04-2026"),
    ("harshada.l", "Pending", "06-04-2026", "06-04-2026"),
    ("harsh.vern", "Pending", "30-04-2026", "04-05-2026"),
    ("ayesha.kar", "Pending", "09-04-2026", "09-04-2026"),
    ("amol@sec", "Pending", "09-03-2026", "09-03-2026"),
    ("prateek.fo", "Approved", "16-03-2026", "16-03-2026"),
    ("altamash@", "Pending", "20-03-2026", "20-03-2026"),
    ("sagar.satp", "Approved", "16-03-2026", "16-03-2026"),
    ("ayesha.kar", "Pending", "27-03-2026", "30-03-2026"),
    ("ayesha.kar", "Pending", "10-04-2026", "10-04-2026"),
    ("pratik.tiwa", "Pending", "21-04-2026", "22-04-2026"),
    ("sagar.satp", "Pending", "13-03-2026", "13-03-2026"),
    ("ashish@se", "Pending", "04-05-2026", "04-05-2026"),
    ("shete.amit", "Pending", "21-04-2026", "21-04-2026"),
    ("prateek.fo", "Pending", "04-05-2026", "04-05-2026"),
    ("ashish.ten", "Pending", "22-04-2026", "22-04-2026"),
    ("arun.thaku", "Pending", "22-04-2026", "22-04-2026"),
    ("harshada.l", "Pending", "24-04-2026", "24-04-2026"),
    ("sagar.satp", "Pending", "04-05-2026", "04-05-2026"),
    ("shailendra", "Pending", "04-05-2026", "05-05-2026"),
    ("shete.amit", "Pending", "10-04-2026", "10-04-2026"),
    ("vaibhav.ku", "Approved", "14-04-2026", "14-04-2026"),
    ("sagar.satp", "Pending", "30-04-2026", "30-04-2026"),
    ("ayesha.kar", "Pending", "04-05-2026", "06-05-2026"),
    ("prateek.fo", "Approved", "30-04-2026", "30-04-2026"),
    ("shete.amit", "Pending", "21-01-2026", "21-01-2026"),
    ("arun.thaku", "Pending", "27-01-2026", "30-01-2026"),
    ("shete.amit", "Pending", "22-01-2026", "22-01-2026"),
    ("harsh.vern", "Approved", "23-02-2026", "25-02-2026"),
    ("rachit.mis", "Pending", "19-01-2026", "19-01-2026"),
    ("ravi.raj@se", "Pending", "06-02-2026", "06-02-2026"),
    ("ayesha.kar", "Pending", "20-01-2026", "20-01-2026"),
    ("surabhi.ch", "Pending", "16-03-2026", "23-03-2026"),
    ("shete.amit", "Pending", "07-01-2026", "07-01-2026"),
    ("harsh.vern", "Pending", "10-02-2026", "10-02-2026"),
    ("ayesha.kar", "Approved", "09-01-2026", "09-01-2026"),
    ("arun.thaku", "Pending", "12-01-2026", "12-01-2026"),
    ("altamash@", "Pending", "28-01-2026", "30-01-2026"),
    ("swaroop.c", "Approved", "14-01-2026", "14-01-2026"),
    ("prateek.fo", "Approved", "09-02-2026", "09-02-2026"),
    ("ashish.ten", "Pending", "20-03-2026", "20-03-2026"),
    ("pratik.tiwa", "Pending", "25-02-2026", "27-02-2026"),
    ("sagar.satp", "Approved", "18-02-2026", "18-02-2026"),
    ("ayesha.kar", "Approved", "27-02-2026", "27-02-2026"),
    ("ashish@se", "Pending", "20-03-2026", "20-03-2026"),
    ("surabhi.ch", "Approved", "02-03-2026", "03-03-2026"),
    ("altamash@", "Pending", "04-02-2026", "04-02-2026"),
    ("rachit.mis", "Pending", "05-02-2026", "05-02-2026"),
    ("shailendra", "Pending", "06-02-2026", "06-02-2026"),
    ("ayesha.kar", "Pending", "10-02-2026", "10-02-2026"),
    ("harsh.vern", "Pending", "23-02-2026", "24-02-2026"),
    ("ravi.raj@se", "Pending", "16-03-2026", "20-03-2026"),
    ("shailendra", "Approved", "28-04-2026", "28-04-2026"),
]

PREFIX_TO_NAME: dict[str, str] = {
    "harsh.vern": "Harsh Verma",
    "ashish@se": "Ashish Modak",
    "surabhi.ch": "Surabhi Choudhary",
    "shailendra": "Shailendra Singh",
    "altamash@": "Altamash Heroli",
    "vaibhav.ku": "Vaibhav Kumbhar",
    "harshada.l": "Harshada Kude",
    "ayesha.kar": "Ayesha Kamde",
    "prateek.fo": "Prateek Fotedar",
    "sagar.satp": "Sagar Satpute",
    "pratik.tiwa": "Pratik Tiwari",
    "shete.amit": "Amit Shete",
    "ashish.ten": "Ashish Temurnikar",
    "arun.thaku": "Arun Thakur",
    "rachit.mis": "Rachit Mishra",
    "ravi.raj@se": "Ravi Raj",
    "swaroop.c": "Swaroop Chavhan",
    "amol@sec": "Amol Mithari",
}

CORE_TEAM: list[str] = [
    "Altamash Heroli",
    "Amit Shete",
    "Amol Mithari",
    "Arun Thakur",
    "Ashish Modak",
    "Ashish Temurnikar",
    "Ayesha Kamde",
    "Harsh Verma",
    "Harshada Kude",
    "Prateek Fotedar",
    "Pratik Tiwari",
    "Rachit Mishra",
    "Ravi Raj",
    "Sagar Satpute",
    "Shailendra Singh",
    "Surabhi Choudhary",
    "Swaroop Chavhan",
    "Vaibhav Kumbhar",
]


def parse_dmy(s: str) -> date:
    return datetime.strptime(s, "%d-%m-%Y").date()


def add_overlap_days(
    target: set[date],
    sprint_start: date,
    sprint_end: date,
    ls: date,
    le: date,
) -> None:
    a = max(sprint_start, ls)
    b = min(sprint_end, le)
    if a > b:
        return
    d = a
    while d <= b:
        if d.weekday() < 5 and d not in COMPANY_HOLIDAYS:
            target.add(d)
        d += timedelta(days=1)


def _pto_weekdays_by_person(
    sprint_start: date, sprint_end: date
) -> dict[str, int]:
    by_person: dict[str, set[date]] = defaultdict(set)
    for prefix, _status, s1, s2 in RAW_LEAVES:
        name = PREFIX_TO_NAME.get(prefix)
        if not name or name not in CORE_TEAM:
            continue
        add_overlap_days(by_person[name], sprint_start, sprint_end, parse_dmy(s1), parse_dmy(s2))
    return {p: len(by_person[p]) for p in CORE_TEAM}


def compute_leave_days(
    sprint_start: date | None = None,
    sprint_end: date | None = None,
) -> dict[str, int]:
    if sprint_start is None or sprint_end is None:
        sprint_start, sprint_end, _ = load_sprint_window()
    return _pto_weekdays_by_person(sprint_start, sprint_end)


def compute_availability_hours(
    sprint_start: date | None = None,
    sprint_end: date | None = None,
    sprint_wd: int | None = None,
) -> dict[str, float]:
    if sprint_start is None or sprint_end is None or sprint_wd is None:
        sprint_start, sprint_end, sprint_wd = load_sprint_window()
    pto_wd = _pto_weekdays_by_person(sprint_start, sprint_end)
    eff_wd = max(0, sprint_wd - len(company_holidays_in_sprint(sprint_start, sprint_end)))
    return {
        person: round(max(0.0, (eff_wd - pto_wd[person]) * 8 * 0.9), 2)
        for person in CORE_TEAM
    }


def main() -> None:
    sprint_start, sprint_end, sprint_wd = load_sprint_window()
    if not SPRINT_META_FILE.is_file():
        print(
            f"Note: {SPRINT_META_FILE.name} not found — using fallback "
            f"{sprint_start} .. {sprint_end}. Run from repo root:\n"
            f"  python fetch_filter_sprint_meta.py sprint-Hanna\n",
            flush=True,
        )
    holidays = company_holidays_in_sprint(sprint_start, sprint_end)
    eff_wd = max(0, sprint_wd - len(holidays))
    pto_wd = _pto_weekdays_by_person(sprint_start, sprint_end)
    print(f"Sprint FILTER: {sprint_start} .. {sprint_end} ({sprint_wd} working days)")
    if holidays:
        print(f"Company holidays in sprint ({len(holidays)}):")
        for d, name in holidays:
            print(f"  {d:%a %d-%b-%Y}  {name}")
        print(f"Effective working days after company holidays: {eff_wd}")
    else:
        print("Company holidays in sprint: 0 (no calendar overlap)")
    total_avail = 0.0
    for person in CORE_TEAM:
        ld = pto_wd[person]
        avail = max(0.0, (eff_wd - ld) * 8 * 0.9)
        total_avail += avail
        if ld:
            print(f"{person}: {ld} PTO weekdays in sprint -> {avail:.2f} h available")
        else:
            print(f"{person}: 0 PTO weekdays in sprint -> {avail:.2f} h available")
    print(f"TOTAL Actual Availability (h): {total_avail:.2f}")


if __name__ == "__main__":
    main()
