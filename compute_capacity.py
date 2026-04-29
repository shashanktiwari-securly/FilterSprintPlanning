"""Sprint-agnostic capacity helper for the FILTER India scrum team.

Reads a sprint folder (``product_FILTER/<sprint>-sprint-data/``) containing
``sprint-meta.json`` (start/end/working_days from Jira) and computes per-person:

* PTO weekdays inside the sprint window (excluding company holidays so we don't
  double-count them).
* Effective working days = sprint working days − company holidays in window.
* Available hours per person = (effective_working_days_for_person − personal_PTO)
  × hours/day × focus factor.

Date-aware roster:

* Amol Mithari joined the FILTER scrum team on 2026-02-20.
* Rachit Mishra's last working day on the team was 2026-02-20.

Anyone outside their employment window for a given day of the sprint loses that
day from their effective working days.

Used by ``build_sprint_analysis.py`` (one workbook per sprint).
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent

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

# (active_from inclusive, active_until inclusive). None means open-ended.
ROSTER_DATES: dict[str, tuple[date | None, date | None]] = {
    "Amol Mithari": (date(2026, 2, 20), None),
    "Rachit Mishra": (None, date(2026, 2, 20)),
}

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


def is_active(person: str, day: date) -> bool:
    """Date-aware roster: returns False for days outside a person's employment window."""
    bounds = ROSTER_DATES.get(person)
    if not bounds:
        return True
    start, end = bounds
    if start is not None and day < start:
        return False
    if end is not None and day > end:
        return False
    return True


def load_sprint_window(meta_path: Path) -> tuple[date, date, int]:
    m = json.loads(meta_path.read_text(encoding="utf-8"))
    start = date.fromisoformat(m["start_date"])
    end = date.fromisoformat(m["end_date"])
    wd = int(m["working_days"])
    return start, end, wd


def company_holidays_in_sprint(
    sprint_start: date, sprint_end: date
) -> list[tuple[date, str]]:
    return sorted(
        (d, name)
        for d, name in COMPANY_HOLIDAYS.items()
        if sprint_start <= d <= sprint_end and d.weekday() < 5
    )


def effective_working_days_in_sprint(sprint_start: date, sprint_end: date) -> int:
    """Sprint-wide effective working days (weekdays minus company holidays)."""
    n = 0
    d = sprint_start
    while d <= sprint_end:
        if d.weekday() < 5 and d not in COMPANY_HOLIDAYS:
            n += 1
        d += timedelta(days=1)
    return n


def effective_working_days_for_person(
    person: str, sprint_start: date, sprint_end: date
) -> int:
    """Per-person working days excluding company holidays AND days outside the
    person's employment window (date-aware roster)."""
    n = 0
    d = sprint_start
    while d <= sprint_end:
        if (
            d.weekday() < 5
            and d not in COMPANY_HOLIDAYS
            and is_active(person, d)
        ):
            n += 1
        d += timedelta(days=1)
    return n


def _add_overlap_days(
    target: set[date],
    person: str,
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
        if (
            d.weekday() < 5
            and d not in COMPANY_HOLIDAYS
            and is_active(person, d)
        ):
            target.add(d)
        d += timedelta(days=1)


def compute_leave_days(
    sprint_start: date, sprint_end: date
) -> dict[str, int]:
    """PTO weekdays per person inside the sprint window, excluding company holidays
    and days the person was not on the team (Amol/Rachit roster dates)."""
    by_person: dict[str, set[date]] = defaultdict(set)
    for prefix, _status, s1, s2 in RAW_LEAVES:
        name = PREFIX_TO_NAME.get(prefix)
        if not name or name not in CORE_TEAM:
            continue
        _add_overlap_days(
            by_person[name],
            name,
            sprint_start,
            sprint_end,
            parse_dmy(s1),
            parse_dmy(s2),
        )
    return {p: len(by_person[p]) for p in CORE_TEAM}


def compute_availability_hours(
    sprint_start: date, sprint_end: date, hpd: float = 8.0, focus: float = 0.9
) -> dict[str, float]:
    pto_wd = compute_leave_days(sprint_start, sprint_end)
    out: dict[str, float] = {}
    for person in CORE_TEAM:
        eff_wd = effective_working_days_for_person(person, sprint_start, sprint_end)
        out[person] = round(max(0.0, (eff_wd - pto_wd[person]) * hpd * focus), 2)
    return out


def active_team(sprint_start: date, sprint_end: date) -> list[str]:
    """Subset of CORE_TEAM whose employment window overlaps any day of the sprint."""
    return [
        p
        for p in CORE_TEAM
        if effective_working_days_for_person(p, sprint_start, sprint_end) > 0
    ]


def main(sprint_folder: str | Path = "product_FILTER/sprint-Hanna-sprint-data") -> None:
    folder = Path(sprint_folder)
    if not folder.is_absolute():
        folder = ROOT / folder
    meta_path = folder / "sprint-meta.json"
    sprint_start, sprint_end, sprint_wd = load_sprint_window(meta_path)
    holidays = company_holidays_in_sprint(sprint_start, sprint_end)
    eff_wd = effective_working_days_in_sprint(sprint_start, sprint_end)
    pto_wd = compute_leave_days(sprint_start, sprint_end)
    print(f"Sprint window: {sprint_start} .. {sprint_end} ({sprint_wd} weekdays)")
    if holidays:
        print(f"Company holidays in sprint ({len(holidays)}):")
        for d, name in holidays:
            print(f"  {d:%a %d-%b-%Y}  {name}")
        print(f"Effective working days after company holidays: {eff_wd}")
    else:
        print("Company holidays in sprint: 0 (no calendar overlap)")
    total = 0.0
    for person in CORE_TEAM:
        person_eff = effective_working_days_for_person(person, sprint_start, sprint_end)
        ld = pto_wd[person]
        avail = max(0.0, (person_eff - ld) * 8 * 0.9)
        total += avail
        roster_note = ""
        if person_eff < eff_wd:
            roster_note = (
                f" [roster-limited: {person_eff} effective days vs sprint {eff_wd}]"
            )
        print(
            f"{person}: {ld} PTO weekdays, {person_eff} effective days "
            f"-> {avail:.2f} h available{roster_note}"
        )
    print(f"TOTAL Actual Availability (h): {total:.2f}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "sprint_folder",
        nargs="?",
        default="product_FILTER/sprint-Hanna-sprint-data",
        help="Folder containing sprint-meta.json",
    )
    args = ap.parse_args()
    main(args.sprint_folder)
