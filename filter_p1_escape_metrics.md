# FILTER — P1 Escape Defect metrics

## Metric definitions (PM)

| Metric | Definition |
|--------|------------|
| **P1 Escape WIP** | Count of issues: project FILTER, type **Escape Defect**, priority **P1**, **status category ≠ Done** (any active state). |
| **WIP cap** | Target: **≤ 3** at any time. Breach if count exceeds cap until triaged. |
| **Monthly opened** | Count of **same** issue type + priority with **created** date in that calendar month (inflow). |

**Snapshot:** 2026-04-20T10:27:35.740798+00:00

## WIP cap check

- **Current open P1 Escape Defects:** 10
- **Limit:** 3
- **Result:** **FAIL — reduce WIP or raise limit**

| Key | Status | Summary |
|-----|--------|---------|
| FILTER-13534 | Open | P1 QA- In prod: Yes, SPAC: "Restrict Google logins to these domains" not working |
| FILTER-13117 | Waiting on support | P1 Escalation-Students bypassing Filter using scrlybrkr |
| FILTER-13105 | QA READY | P1 Escalation-Looking for solution for HTML Editor vulnerabilities  |
| FILTER-13086 | Open | P1 Escalation-Fix reCAPTCHA / google.com/recaptcha failures when Securly SmartPA |
| FILTER-12476 | In Progress | P1 Escalation-Extension Bypass - Opening new tab |
| FILTER-12262 | In Progress | P1 Escalation-Spike in Google Captchas starting 02.24.26 |
| FILTER-12119 | In Progress | P1 Escalation-Investigate and address the use of about:blank pages as a filter l |
| FILTER-11610 | In Progress | P1 Escalation-CORs Errors at BlueBeam and Boomerang S3 Amazon domains \| St. Vra |
| FILTER-10053 | Open | Chrome Extension is causing specific form not to load |
| FILTER-7666 | QA READY | P1 Escalation-File downloading in Image Google Search |

## Monthly inflow (2026) — P1 Escape Defects created

| Month | Opened (created in month) |
|-------|----------------------------:|
| Jan 2026 | 6 |
| Feb 2026 | 9 |
| Mar 2026 | 5 |
| Apr 2026 | 8 |
| May 2026 | 0 |
| Jun 2026 | 0 |
| Jul 2026 | 0 |
| Aug 2026 | 0 |
| Sep 2026 | 0 |
| Oct 2026 | 0 |
| Nov 2026 | 0 |
| Dec 2026 | 0 |

## JQL reference

**WIP (concurrent):**
```
project = FILTER AND issuetype = "Escape Defect" AND priority = P1 AND statusCategory != Done
```
