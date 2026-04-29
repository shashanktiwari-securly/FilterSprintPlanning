# P1 Escape Defect metrics — all products (comparison)

**Year:** 2026 · **WIP cap (comparison):** ≤ 3 · **Snapshot:** 2026-04-20T10:58:36.187063+00:00

## WIP vs cap (concurrent open)

| Product | Jira | WIP | Cap | Status |
|---------|------|----:|----:|--------|
| AIChat | `AICHAT` | 0 | 3 | **PASS** |
| FLEX & COM | `FLEX` | 2 | 3 | **PASS** |
| PASS | `PASS` | 0 | 3 | **PASS** |
| Platform | `PLATFORM` | 0 | 3 | **PASS** |
| product_aware | `AWARE` | 2 | 3 | **PASS** |
| product_FILTER | `FILTER` | 10 | 3 | **FAIL** |
| product_home | `HOME` | 0 | 3 | **PASS** |
| product_MDM_CLASSROOM | `MDMCLASS` | 0 | 3 | **PASS** |
| product_oncall | `PRODUCT24` | 0 | 3 | **PASS** |
| product_RESPOND | `RESP` | 0 | 3 | **PASS** |

## Monthly inflow (2026) — created per month (P1 Escape Defect)

| Product | Jira | Jan 2026 | Feb 2026 | Mar 2026 | Apr 2026 | May 2026 | Jun 2026 | Jul 2026 | Aug 2026 | Sep 2026 | Oct 2026 | Nov 2026 | Dec 2026 | YTD |
|---------|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:| :---: |
| AIChat | `AICHAT` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| FLEX & COM | `FLEX` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| PASS | `PASS` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Platform | `PLATFORM` | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| product_aware | `AWARE` | 2 | 0 | 5 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 |
| product_FILTER | `FILTER` | 6 | 9 | 5 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 |
| product_home | `HOME` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| product_MDM_CLASSROOM | `MDMCLASS` | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| product_oncall | `PRODUCT24` | 3 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| product_RESPOND | `RESP` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Open issues by product (WIP detail)

### AIChat (`AICHAT`) — WIP 0

_None._

### FLEX & COM (`FLEX`) — WIP 2

| Key | Status | Summary |
|-----|--------|---------|
| FLEX-3893 | In Progress | P1 Escalation-Load times for pages taking a long time - Herndon HS & James W Robinson (Fairfax Count |
| FLEX-3555 | QA in Progress | (Fixed in phases) P1 Escalation-Load time for pages taking longer than normal - Multiple schools |

### PASS (`PASS`) — WIP 0

_None._

### Platform (`PLATFORM`) — WIP 0

_None._

### product_aware (`AWARE`) — WIP 2

| Key | Status | Summary |
|-----|--------|---------|
| AWARE-7109 | In Progress | On expiry of login session, error pop appears which does not get disappear on clicking cancle or ok  |
| AWARE-7084 | In Progress | MT User  and Support tool users not able to access Aware Safety Console. |

### product_FILTER (`FILTER`) — WIP 10

| Key | Status | Summary |
|-----|--------|---------|
| FILTER-13534 | Open | P1 QA- In prod: Yes, SPAC: "Restrict Google logins to these domains" not working for Gmail (mail.goo |
| FILTER-13117 | Waiting on support | P1 Escalation-Students bypassing Filter using scrlybrkr |
| FILTER-13105 | QA READY | P1 Escalation-Looking for solution for HTML Editor vulnerabilities  |
| FILTER-13086 | Open | P1 Escalation-Fix reCAPTCHA / google.com/recaptcha failures when Securly SmartPAC (and related proxy |
| FILTER-12476 | In Progress | P1 Escalation-Extension Bypass - Opening new tab |
| FILTER-12262 | In Progress | P1 Escalation-Spike in Google Captchas starting 02.24.26 |
| FILTER-12119 | In Progress | P1 Escalation-Investigate and address the use of about:blank pages as a filter loophole |
| FILTER-11610 | In Progress | P1 Escalation-CORs Errors at BlueBeam and Boomerang S3 Amazon domains \| St. Vrain |
| FILTER-10053 | Open | Chrome Extension is causing specific form not to load |
| FILTER-7666 | QA READY | P1 Escalation-File downloading in Image Google Search |

### product_home (`HOME`) — WIP 0

_None._

### product_MDM_CLASSROOM (`MDMCLASS`) — WIP 0

_None._

### product_oncall (`PRODUCT24`) — WIP 0

_None._

### product_RESPOND (`RESP`) — WIP 0

_None._

## JQL (WIP)

```
project = <KEY> AND issuetype = "Escape Defect" AND priority = P1 AND statusCategory != Done
```
