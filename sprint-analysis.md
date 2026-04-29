---
name: sprint-analysis-workbook
description: Generates a sprint analysis Excel workbook (Capacity vs Delivery, Per-person Delivery, Completed, Not Completed, Removed) from Jira data, applying Parul's standardised conventions. Use when the user asks for a sprint analysis, sprint retrospective spreadsheet, sprint closeout, or any "<sprint name> analysis" workbook for any of her products (Cases, On-call OR, Home, Respond, etc.). Trigger phrases include "sprint analysis", "sprint retro xlsx", "close out sprint", "sprint review excel", "<sprint-name> analysis".
---

# Sprint analysis workbook

Build a single Excel file at the workspace root named `<Product> Sprint <Name> Analysis.xlsx` (or whatever convention the active workspace uses).

## Required inputs (only ask for these)

1. **Sprint name** — e.g. `Hanna`, `Sprint A`, `sprint-Cases-Hanna`. If the Jira sprint id is also known, accept it.
2. **Core team availability** — per-person available hours in the sprint, e.g.

   ```
   Amit Shirke         80
   Dhruv Raj           80
   Gaurav Lonkar       72
   Omkar Joshi         80
   Omkarnath Panage    72
   Suhas Pawar         80
   Goutham Balashanmugam  64
   Manshi Jain         80
   ```

   The names in this table **define the core delivery team for this sprint**. Anyone not listed is excluded from every sheet of the workbook.

Everything else (sprint dates, total FTE, ideal capacity, leaves) is inferred from these two inputs plus Jira metadata. If anything else is unclear, ask only about that one thing — don't re-litigate already-decided conventions.

## Workbook structure (exactly 5 tabs, in this order)

1. `Capacity vs Delivery`
2. `Per-person Delivery`
3. `Completed`
4. `Not Completed`
5. `Removed`

No other tabs. No "Summary", "Goal & Takeaways", "Spillover", or "Trend" tabs unless the user explicitly asks.

## Hours only — no counts

Every headline metric uses one of two source fields:

- `Time Spent` — but **only the hours logged during the current sprint window** (not Jira's cumulative `timespent`).
- `Original Estimate`.

Do not add "count of tasks" anywhere.

## Bucketing (apply top-to-bottom; first match wins)

| Bucket | Status set | Headline column |
|---|---|---|
| `Removed` | items moved out of the sprint mid-flight | **Original Estimate** |
| `Completed` | `statusCategory = done` **OR** status ∈ {Resolved, Code Review} | **Time Spent (in-sprint only)** |
| `Not Completed` | status ∈ {In Progress, Open, Ready for QA, Reopened} | **Original Estimate** |

Resolved + Code Review live on the Completed sheet even though Jira's `statusCategory` for them isn't `done`.

## Time-handling rule (all 3 detail sheets)

Hybrid worklog model:

- **Single-sprint ticket** — keep as-is. `Time Spent` = Jira `timespent` (or `aggregatetimespent` fallback when null).
- **Multi-sprint ticket** — fetch the issue worklog and:
  - Drop the row if no worklog entry has `started ∈ [sprintStart, sprintEnd]`.
  - Otherwise, replace `Time Spent` with the SUM of worklog entries whose `started` falls inside the sprint window.

**Worklog fetch path**: the Atlassian MCP doesn't expose a worklog tool. Use `getJiraIssue` requesting `fields: ["worklog", ...]`, or fall through to the REST endpoint `/rest/api/3/issue/{key}/worklog` via the generic `fetch` MCP tool. Only do this for multi-sprint rows — single-sprint rows don't need the round-trip.

## `Capacity vs Delivery` tab

Required rows in this order:

| Row | Source |
|---|---|
| `Sprint length (working days)` | yellow input — default 10 |
| `Hours per working day (nominal)` | yellow input — default 8 |
| `Focus factor (productive fraction)` | yellow input — **default 0.9** ("90% — what SLT expects") |
| `Effective hours per FTE per sprint` | formula = days × hrs/day × focus |
| `Allocated FTE` | yellow input — **count of names in the availability table** (e.g. 8 for Hanna, 7 for Isaias). Manual override, not a formula sum from a separate team table. |
| `Ideal capacity for the sprint (hrs)` | formula = effective hrs × allocated FTE |
| `Actual Availability` | typed number = SUM of per-person availability from the input table (= Ideal − leaves) |
| `Completed` | Σ Time Spent (in-sprint) on the Completed sheet |
| `Not Completed` | Σ Original Estimate on the Not Completed sheet |
| `Removed` | Σ Original Estimate on the Removed sheet |

Each delivery row gets `% of Ideal` (i.e. `value / Ideal capacity`) and a Rating against:

- ≥ 85% → `On Target` (green `FFC6EFCE` / font `FF006100`)
- 70–85% → `Below Target` (amber `FFFFEB9C` / font `FF9C5700`)
- < 70% → `Significantly Below` (red `FFFFC7CE` / font `FF9C0006`)

Also include a brief "Assumptions & caveats" block at the bottom. Keep it short — 4–6 bullets max.

## `Per-person Delivery` tab

Columns, exactly:

`Assignee | Completed (hrs) | Not Completed (hrs) | Removed (hrs) | Efficiency | Available (hrs)`

- One row per name in the availability input table. Do not add other assignees, even if they show up in Jira.
- `Available (hrs)` = the value from the input table.
- `Efficiency = Completed / Available` per row. Don't cap above 100% — over-delivery is a meaningful signal.
- TOTAL row at the bottom: sum every hours column; `Available` = SUM of per-person availability (must equal `Actual Availability` on Capacity tab); `Efficiency` = total Completed / total Available.
- Apply the same green/amber/red bands to the Efficiency cells as on the Capacity tab.

## Detail sheets (`Completed`, `Not Completed`, `Removed`)

Standard columns (mirror the OR Q1 layout):

`Issue Type | Issue key | Summary | Parent key | Parent type | Assignee | Status | Resolution | Priority | Created | Resolved | Updated | Sprint | Time Spent | Original Estimate | Project | Labels | Blockers`

- `Issue key` and `Parent key` are hyperlinks to `https://<jira-host>/browse/<key>`.
- `Time Spent` reflects in-sprint hours per the time-handling rule above.
- `Original Estimate` always shown alongside; this is what the Not Completed and Removed totals roll up to.
- Sort by Assignee then Issue key. Wrap text on Summary. Auto-filter on row 1.

## Workflow

```
Task progress:
- [ ] Confirm sprint name + per-person availability table
- [ ] Look up sprint id and dates via JQL (sprint = "<name>" or sprint = <id>)
- [ ] Pull all in-sprint issues (paginate) — ALL projects, ALL assignees
- [ ] Pull the Sprint Report's "Issues removed from the sprint" list
      (best-effort: snapshot diff against any local jira-history.json;
      ask the user to paste keys if a clean list isn't available —
      "Sprint was" is no longer supported by enhanced JQL)
- [ ] For each multi-sprint issue, fetch worklogs and apply the in-sprint filter
- [ ] Drop every issue whose assignee is not in the availability table
- [ ] Apply bucketing rules (Removed → Completed [incl. Resolved + Code Review] → Not Completed)
- [ ] Build the 5-tab workbook with ExcelJS
- [ ] Save .xlsx at the workspace root and the build script under <product>/<sprint>-sprint-data/
- [ ] Print summary to console: sprint, completed hrs, not-completed hrs, removed hrs, efficiency
```

## Number formats (must match exactly)

Excel `numFmt` values to use — non-negotiable, otherwise downstream parsers and conditional logic break:

| Cell type | `numFmt` |
|---|---|
| Working days, Allocated FTE (true integer inputs) | `0` |
| All hours cells (capacity, delivery, per-person, detail-sheet Time Spent / Original Estimate) | `0.00` |
| Focus factor (productive fraction) | `0.00` |
| `% of Ideal`, `Efficiency` | `0.0%` |
| Dates (Created / Resolved / Updated) | plain `YYYY-MM-DD` strings — do **not** apply Excel date formats |

❌ Never use `0.##` for hours — it renders 8 as `8.` (trailing dot, no decimals) which trips parsers.
✅ Always render hours as `8.00`, `4.50`, `0.25`, etc.

If a numeric cell would otherwise be 0 *and* there's no real value behind it (e.g. no time logged, no estimate), prefer leaving the cell empty over writing `0.00` — but never leave a partially-formatted cell.

## Build-script convention

Always write a re-runnable Node.js script at `<product>/<sprint>-sprint-data/build-<sprint>-analysis.js` so the user can refresh after status changes:

- Reuse ExcelJS from any nearby `node_modules` (e.g. `or-sprint-data/node_modules/exceljs`); do not require a fresh `npm install` per sprint.
- Save the raw paginated Jira responses next to the script as `sprint<id>-page<N>.json` so the analysis is reproducible.
- Output path: workspace-root `<Product> Sprint <Name> Analysis.xlsx`.

## Inputs to ask for (only when missing)

If the user has not provided them already, ask **once** for these — and only these:

- Sprint name or sprint Jira id (one or the other is enough).
- Per-person availability table for the sprint (names → hours).

If a `team-composition.md` exists in the workspace, use it for default availability (10 working days × 8 h × allocation, minus any leaves the user mentions). But the availability table the user provides always wins.

## Anti-patterns to avoid

- ❌ Adding count columns or "issues delivered" totals — hours only.
- ❌ Rolling Resolved or Code Review into Not Completed — they belong in Completed.
- ❌ Using cumulative `timespent` for multi-sprint tickets — must be in-sprint worklog only.
- ❌ Including assignees who aren't in the availability table — drop them.
- ❌ Auto-summing the Allocated FTE from a separate team table — it's a manual override (count of names in availability).
- ❌ Adding Goal / Summary / Trend / Spillover tabs unless explicitly asked.
- ❌ Re-asking for sprint window dates, focus factor, or rating bands — they're fixed defaults above.
