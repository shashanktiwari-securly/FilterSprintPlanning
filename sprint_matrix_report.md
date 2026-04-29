# Sprint matrix — planned scope vs completed (Jira)

**Generated:** see JSON `generated_at`.

## Methodology

- **Planned (scope):** issues matching `project = X AND sprint in (...)` for the named sprint(s). For completed sprints, this matches Jira’s sprint assignment (final scope including items added mid-sprint).
- **Completed:** issues whose **status category** is **Done** (includes Closed, Done, Closed without action, etc.).
- **Primary track metric — Original estimate (hours):** sum of Jira **Original estimate** (`timeoriginalestimate`, seconds → hours) across all in-scope issues vs sum on **Done** issues. Issues with no estimate contribute **0** to both sums. **Est. done %** = done hours ÷ planned hours.
- **Story points (reference only):** sum of `customfield_10005` where populated — not used as the delivery track bar.
- **PHP / Go migration (GM):** not a separate row; work is executed in other teams’ sprints. Issues filed under **FILTER**, **RESP**, etc. appear in those product queries; use `project = GM` in Jira for migration-only backlog.

## Project key mapping

| Report label | Jira key | Jira project name |
|--------------|----------|-------------------|
| AIChat | AICHAT | Product_AIChat |
| FLEX & COM | FLEX | Flex |
| PASS | PASS | Pass |
| Platform | PLATFORM | Platform |
| product_aware | AWARE | product_AWARE |
| product_FILTER | FILTER | product_FILTER |
| product_home | HOME | product_HOME |
| product_MDM_CLASSROOM | MDMCLASS | product_MDM_CLASSROOM |
| product_oncall | PRODUCT24 | product_oncall |
| product_RESPOND | RESP | product_RESPOND |

## Matrix

| Product | Month | Sprint(s) | Scope | Done | Issue done % | Est. h planned | Est. h done | Est. done % | SP ref |
|---------|-------|-------------|------:|-----:|-------------:|---------------:|------------:|------------:|--------|
| product_home | 2026-01 | sprint-Home-Arthur | 123 | 122 | 99.2% | 504.8 | 496.8 | 98.4 | 0.0/0.0 () |
| product_home | 2026-01 | sprint-Home-Bertha | 137 | 137 | 100.0% | 716.9 | 716.9 | 100.0 | 0.0/0.0 () |
| product_home | 2026-02 | sprint-Home-Cristobal | 98 | 98 | 100.0% | 431.66 | 431.66 | 100.0 | 0.0/0.0 () |
| product_home | 2026-02 | sprint-Home-Dolly | 65 | 65 | 100.0% | 415.58 | 415.58 | 100.0 | 0.0/0.0 () |
| product_home | 2026-03 | sprint-Home-Edouard | 147 | 145 | 98.6% | 779.0 | 771.0 | 99.0 | 48.0/48.0 (100.0) |
| product_home | 2026-03 | sprint-Home-Fay | 78 | 76 | 97.4% | 402.58 | 394.58 | 98.0 | 0.0/0.0 () |
| product_home | 2026-01 | sprint-Aware-Arthur | 0 | 0 | 0.0% | 0.0 | 0.0 |  | 0.0/0.0 () |
| product_MDM_CLASSROOM | 2026-01 | sprint-MDMCL-Arthur | 124 | 118 | 95.2% | 500.69 | 484.69 | 96.8 | 0.0/0.0 () |
| product_MDM_CLASSROOM | 2026-01 | sprint-MDMCL-Bertha | 156 | 142 | 91.0% | 786.33 | 694.33 | 88.3 | 0.0/0.0 () |
| product_MDM_CLASSROOM | 2026-02 | sprint-MDMCL-Cristobal | 196 | 176 | 89.8% | 1037.75 | 925.75 | 89.2 | 0.0/0.0 () |
| product_MDM_CLASSROOM | 2026-02 | sprint-MDMCL-Dolly | 304 | 279 | 91.8% | 1292.51 | 1051.51 | 81.4 | 0.0/0.0 () |
| product_MDM_CLASSROOM | 2026-03 | sprint-MDMCL-Edouard | 235 | 180 | 76.6% | 998.09 | 694.34 | 69.6 | 0.0/0.0 () |
| product_MDM_CLASSROOM | 2026-03 | sprint-MDMCL-Fay | 219 | 146 | 66.7% | 1251.51 | 841.76 | 67.3 | 0.0/0.0 () |
| product_oncall | 2026-01 | sprint-Arthur | 93 | 80 | 86.0% | 397.5 | 353.5 | 88.9 | 30.0/30.0 (100.0) |
| product_oncall | 2026-01 | sprint-Bertha | 159 | 144 | 90.6% | 783.67 | 745.67 | 95.2 | 73.0/68.0 (93.2) |
| product_oncall | 2026-02 | sprint-Cristobal | 68 | 68 | 100.0% | 257.5 | 257.5 | 100.0 | 67.0/67.0 (100.0) |
| product_oncall | 2026-02 | sprint-Dolly | 73 | 72 | 98.6% | 279.67 | 279.17 | 99.8 | 13.0/12.0 (92.3) |
| product_oncall | 2026-03 | sprint-Cases-Edouard | 69 | 69 | 100.0% | 161.75 | 161.75 | 100.0 | 26.0/26.0 (100.0) |
| product_oncall | 2026-03 | sprint-Cases-Fay | 110 | 102 | 92.7% | 360.75 | 318.75 | 88.4 | 26.0/26.0 (100.0) |
| product_RESPOND | 2026-01 | sprint-Arthur | 49 | 36 | 73.5% | 188.0 | 188.0 | 100.0 | 43.0/43.0 (100.0) |
| product_RESPOND | 2026-01 | sprint-Bertha | 55 | 42 | 76.4% | 200.0 | 200.0 | 100.0 | 43.0/43.0 (100.0) |
| product_RESPOND | 2026-02 | sprint-Cristobal | 4 | 4 | 100.0% | 17.0 | 17.0 | 100.0 | 5.0/5.0 (100.0) |
| product_RESPOND | 2026-02 | sprint-Dolly | 6 | 6 | 100.0% | 29.0 | 29.0 | 100.0 | 6.0/6.0 (100.0) |
| product_RESPOND | 2026-03 | sprint-Cases-Edouard | 9 | 9 | 100.0% | 84.0 | 84.0 | 100.0 | 12.0/12.0 (100.0) |
| product_RESPOND | 2026-03 | sprint-Cases-Fay | 35 | 35 | 100.0% | 233.0 | 233.0 | 100.0 | 29.0/29.0 (100.0) |
| product_FILTER | 2026-01 | sprint-Arthur | 156 | 129 | 82.7% | 561.58 | 542.08 | 96.5 | 0.0/0.0 () |
| product_FILTER | 2026-01 | sprint-Bertha | 227 | 201 | 88.5% | 1012.0 | 1004.5 | 99.3 | 137.0/137.0 (100.0) |
| product_FILTER | 2026-02 | sprint-Cristobal | 167 | 163 | 97.6% | 886.5 | 874.5 | 98.6 | 9.0/9.0 (100.0) |
| product_FILTER | 2026-02 | sprint-Dolly | 63 | 57 | 90.5% | 478.5 | 428.5 | 89.6 | 13.0/13.0 (100.0) |
| product_FILTER | 2026-03 | sprint-Edouard | 296 | 236 | 79.7% | 1708.0 | 1392.0 | 81.5 | 0.0/0.0 () |
| product_FILTER | 2026-03 | sprint-Fay | 184 | 161 | 87.5% | 882.5 | 812.5 | 92.1 | 0.0/0.0 () |
| PASS | 2026-01 | PASS Sprint 40 | 133 | 109 | 82.0% | 763.5 | 581.5 | 76.2 | 405.0/376.0 (92.8) |
| PASS | 2026-01 | PASS Sprint 41 | 154 | 128 | 83.1% | 930.5 | 724.5 | 77.9 | 368.0/347.0 (94.3) |
| PASS | 2026-02 | PASS Sprint 42 | 166 | 149 | 89.8% | 908.0 | 734.0 | 80.8 | 286.0/265.0 (92.7) |
| PASS | 2026-02 | PASS Sprint 43 | 155 | 123 | 79.4% | 922.5 | 598.5 | 64.9 | 357.0/318.0 (89.1) |
| PASS | 2026-03 | PASS Sprint 44 | 190 | 146 | 76.8% | 996.0 | 609.5 | 61.2 | 488.0/449.0 (92.0) |
| PASS | 2026-03 | PASS Sprint 45 | 157 | 108 | 68.8% | 792.5 | 356.0 | 44.9 | 486.0/447.0 (92.0) |
| FLEX & COM | 2026-01 | FLEX/COM Sprint 128 | 42 | 42 | 100.0% | 270.49 | 270.49 | 100.0 | 0.0/0.0 () |
| FLEX & COM | 2026-01 | FLEX/COM Sprint 129 | 69 | 60 | 87.0% | 654.33 | 593.33 | 90.7 | 0.0/0.0 () |
| FLEX & COM | 2026-02 | FLEX/COM Sprint 130 | 56 | 48 | 85.7% | 535.0 | 474.0 | 88.6 | 0.0/0.0 () |
| FLEX & COM | 2026-02 | FLEX/COM Sprint 131 | 42 | 36 | 85.7% | 430.0 | 366.0 | 85.1 | 0.0/0.0 () |
| FLEX & COM | 2026-03 | FLEX/COM Sprint 132 | 62 | 53 | 85.5% | 585.0 | 469.0 | 80.2 | 0.0/0.0 () |
| FLEX & COM | 2026-03 | FLEX/COM Sprint 133 | 42 | 38 | 90.5% | 483.0 | 439.0 | 90.9 | 0.0/0.0 () |
| product_aware | 2026-01 | sprint-Aware-Bertha | 85 | 79 | 92.9% | 293.0 | 249.0 | 85.0 | 0.0/0.0 () |
| product_aware | 2026-02 | sprint-Aware-Cristobal | 66 | 66 | 100.0% | 240.0 | 240.0 | 100.0 | 0.0/0.0 () |
| product_aware | 2026-02 | sprint-Aware-Dolly | 86 | 86 | 100.0% | 281.5 | 281.5 | 100.0 | 4.0/4.0 (100.0) |
| product_aware | 2026-03 | sprint-Aware-Edouard | 75 | 70 | 93.3% | 254.0 | 205.0 | 80.7 | 0.0/0.0 () |
| product_aware | 2026-03 | sprint-Aware-Fay | 38 | 34 | 89.5% | 180.0 | 148.0 | 82.2 | 8.0/8.0 (100.0) |
| AIChat | 2026-01 | sprint-AIChat-Zephyr, sprint-AIChat-Arthur | 48 | 48 | 100.0% | 370.5 | 370.5 | 100.0 | 2.0/2.0 (100.0) |
| AIChat | 2026-02 | sprint-AIChat-Bertha, sprint-AIChat-38, sprint-AIChat-39 | 11 | 10 | 90.9% | 63.0 | 63.0 | 100.0 | 0.0/0.0 () |
| AIChat | 2026-03 | sprint-AIChat-41, sprint-AIChat-42, sprint-AIChat-43, sprint-AIChat-44, sprint-AIChat-45 | 47 | 41 | 87.2% | 350.0 | 342.0 | 97.7 | 0.0/0.0 () |
| Platform | 2026-01 | sprint-Platform-Arthur, sprint-Platform-Bertha | 18 | 17 | 94.4% | 59.0 | 59.0 | 100.0 | 0.0/0.0 () |
| Platform | 2026-02 | sprint-Platform-Cristobal, sprint-Platform-Dolly | 21 | 20 | 95.2% | 125.0 | 125.0 | 100.0 | 0.0/0.0 () |
| Platform | 2026-03 | sprint-Platform-Edouard, sprint-Platform-Fay | 77 | 75 | 97.4% | 483.0 | 483.0 | 100.0 | 0.0/0.0 () |

## JQL index

- **product_home** 2026-01 — `project = HOME AND sprint in ("sprint-Home-Arthur")`
- **product_home** 2026-01 — `project = HOME AND sprint in ("sprint-Home-Bertha")`
- **product_home** 2026-02 — `project = HOME AND sprint in ("sprint-Home-Cristobal")`
- **product_home** 2026-02 — `project = HOME AND sprint in ("sprint-Home-Dolly")`
- **product_home** 2026-03 — `project = HOME AND sprint in ("sprint-Home-Edouard")`
- **product_home** 2026-03 — `project = HOME AND sprint in ("sprint-Home-Fay")`
- **product_home** 2026-01 — `project = HOME AND sprint in ("sprint-Aware-Arthur")`
- **product_MDM_CLASSROOM** 2026-01 — `project = MDMCLASS AND sprint in ("sprint-MDMCL-Arthur")`
- **product_MDM_CLASSROOM** 2026-01 — `project = MDMCLASS AND sprint in ("sprint-MDMCL-Bertha")`
- **product_MDM_CLASSROOM** 2026-02 — `project = MDMCLASS AND sprint in ("sprint-MDMCL-Cristobal")`
- **product_MDM_CLASSROOM** 2026-02 — `project = MDMCLASS AND sprint in ("sprint-MDMCL-Dolly")`
- **product_MDM_CLASSROOM** 2026-03 — `project = MDMCLASS AND sprint in ("sprint-MDMCL-Edouard")`
- **product_MDM_CLASSROOM** 2026-03 — `project = MDMCLASS AND sprint in ("sprint-MDMCL-Fay")`
- **product_oncall** 2026-01 — `project = PRODUCT24 AND sprint in ("sprint-Arthur")`
- **product_oncall** 2026-01 — `project = PRODUCT24 AND sprint in ("sprint-Bertha")`
- **product_oncall** 2026-02 — `project = PRODUCT24 AND sprint in ("sprint-Cristobal")`
- **product_oncall** 2026-02 — `project = PRODUCT24 AND sprint in ("sprint-Dolly")`
- **product_oncall** 2026-03 — `project = PRODUCT24 AND sprint in ("sprint-Cases-Edouard")`
- **product_oncall** 2026-03 — `project = PRODUCT24 AND sprint in ("sprint-Cases-Fay")`
- **product_RESPOND** 2026-01 — `project = RESP AND sprint in ("sprint-Arthur")`
- **product_RESPOND** 2026-01 — `project = RESP AND sprint in ("sprint-Bertha")`
- **product_RESPOND** 2026-02 — `project = RESP AND sprint in ("sprint-Cristobal")`
- **product_RESPOND** 2026-02 — `project = RESP AND sprint in ("sprint-Dolly")`
- **product_RESPOND** 2026-03 — `project = RESP AND sprint in ("sprint-Cases-Edouard")`
- **product_RESPOND** 2026-03 — `project = RESP AND sprint in ("sprint-Cases-Fay")`
- **product_FILTER** 2026-01 — `project = FILTER AND sprint in ("sprint-Arthur")`
- **product_FILTER** 2026-01 — `project = FILTER AND sprint in ("sprint-Bertha")`
- **product_FILTER** 2026-02 — `project = FILTER AND sprint in ("sprint-Cristobal")`
- **product_FILTER** 2026-02 — `project = FILTER AND sprint in ("sprint-Dolly")`
- **product_FILTER** 2026-03 — `project = FILTER AND sprint in ("sprint-Edouard")`
- **product_FILTER** 2026-03 — `project = FILTER AND sprint in ("sprint-Fay")`
- **PASS** 2026-01 — `project = PASS AND sprint in ("PASS Sprint 40")`
- **PASS** 2026-01 — `project = PASS AND sprint in ("PASS Sprint 41")`
- **PASS** 2026-02 — `project = PASS AND sprint in ("PASS Sprint 42")`
- **PASS** 2026-02 — `project = PASS AND sprint in ("PASS Sprint 43")`
- **PASS** 2026-03 — `project = PASS AND sprint in ("PASS Sprint 44")`
- **PASS** 2026-03 — `project = PASS AND sprint in ("PASS Sprint 45")`
- **FLEX & COM** 2026-01 — `project = FLEX AND sprint in ("FLEX/COM Sprint 128")`
- **FLEX & COM** 2026-01 — `project = FLEX AND sprint in ("FLEX/COM Sprint 129")`
- **FLEX & COM** 2026-02 — `project = FLEX AND sprint in ("FLEX/COM Sprint 130")`
- **FLEX & COM** 2026-02 — `project = FLEX AND sprint in ("FLEX/COM Sprint 131")`
- **FLEX & COM** 2026-03 — `project = FLEX AND sprint in ("FLEX/COM Sprint 132")`
- **FLEX & COM** 2026-03 — `project = FLEX AND sprint in ("FLEX/COM Sprint 133")`
- **product_aware** 2026-01 — `project = AWARE AND sprint in ("sprint-Aware-Bertha")`
- **product_aware** 2026-02 — `project = AWARE AND sprint in ("sprint-Aware-Cristobal")`
- **product_aware** 2026-02 — `project = AWARE AND sprint in ("sprint-Aware-Dolly")`
- **product_aware** 2026-03 — `project = AWARE AND sprint in ("sprint-Aware-Edouard")`
- **product_aware** 2026-03 — `project = AWARE AND sprint in ("sprint-Aware-Fay")`
- **AIChat** 2026-01 — `project = AICHAT AND sprint in ("sprint-AIChat-Zephyr", "sprint-AIChat-Arthur")`
- **AIChat** 2026-02 — `project = AICHAT AND sprint in ("sprint-AIChat-Bertha", "sprint-AIChat-38", "sprint-AIChat-39")`
- **AIChat** 2026-03 — `project = AICHAT AND sprint in ("sprint-AIChat-41", "sprint-AIChat-42", "sprint-AIChat-43", "sprint-AIChat-44", "sprint-AIChat-45")`
- **Platform** 2026-01 — `project = PLATFORM AND sprint in ("sprint-Platform-Arthur", "sprint-Platform-Bertha")`
- **Platform** 2026-02 — `project = PLATFORM AND sprint in ("sprint-Platform-Cristobal", "sprint-Platform-Dolly")`
- **Platform** 2026-03 — `project = PLATFORM AND sprint in ("sprint-Platform-Edouard", "sprint-Platform-Fay")`
