# Securly PjM Skills (consolidated)

Single reference for **Securly India / Filter** project management and agile delivery.  
Sourced from Cursor skills under `~/.cursor/skills/`.

## Contents

1. [Part 1 — Project Manager: Sprint and Team Context](#part-1--project-manager-sprint-and-team-context) (`project-manager-sprint-context`)
2. [Part 2 — Securly Filter: Project Manager Workflow](#part-2--securly-filter-project-manager-workflow) (`securly-filter-pm-workflow`)
3. [Part 3 — Agile Delivery Manager](#part-3--agile-delivery-manager) (`agile-delivery-manager`)
4. [Part 4 — Reference: Detailed Jira Descriptions (worked example)](#part-4--reference-detailed-jira-descriptions-worked-example)
5. [Part 5 — Professional frameworks: PMP, PRINCE2, Scrum Master](#part-5--professional-frameworks-pmp-prince2-scrum-master)
6. [Part 6 — Historical Jira data for Dev / QA / Automation estimates](#part-6--historical-jira-data-for-dev--qa--automation-estimates)

**How to use with an AI assistant:** Paste a section or say “follow Securly PjM Skills Part 2 + Part 3.” For Filter, **Part 2 overrides** generic Jira/subtask rules where they conflict with **Part 3.** Use **Part 5** when you want **PMI/PMP-style integration and risk thinking**, **PRINCE2-style governance and staged control**, or **explicit Scrum Master accountabilities** layered on top of Parts 1–4. Use **Part 6** when estimating **Dev, Manual QA, and Automation** subtasks from **local historical Jira exports** (reference sprints below).

---

## Part 1 — Project Manager: Sprint and Team Context

*Cursor skill name:* `project-manager-sprint-context`

### Sprint cadence

- **Length**: 15-day sprint cycle (team convention).
- **Boundaries**: Sprint **starts on Tuesday** and **ends on Monday** (inclusive end date is the closing Monday).
- **Rolling schedule**: The next sprint typically **starts the Tuesday immediately after** the previous sprint’s end Monday.

#### Reference example (illustrative)


| Phase        | Date       | Weekday |
| ------------ | ---------- | ------- |
| Sprint start | 2026-04-14 | Tuesday |
| Sprint end   | 2026-04-27 | Monday  |


Use this pattern to infer adjacent sprint windows when the user gives one anchor date.

### Team composition

When breaking down work, estimating, or assigning owners, assume these roles:


| Role                        | Focus                                                                           |
| --------------------------- | ------------------------------------------------------------------------------- |
| **FrontEnd Developer**      | Angular web UI, UX implementation, browser-facing Filter client                 |
| **Backend (www) developer** | Web-facing services (**Go**, **PHP**)                                           |
| **BackEnd developer**       | Core path: **DNS**, **SPAC**, **Squid**, **Rust** and related server components |
| **Extension developer**     | Browser extension codebase and release mechanics                                |
| **Manual QA**               | Exploratory testing, test cases, regression, sign-off on builds                 |
| **Automation Testing**      | SDET: automated tests, CI, flakiness and maintenance                            |


Tag tasks and risks with the **most appropriate single owner**; call out **pairing or handoffs** (e.g. FrontEnd ↔ BackEnd (www) for API contracts; Extension ↔ BackEnd for shared behavior; Manual QA ↔ Automation Testing for coverage). **Named people and skills** are in **Part 2** of this document.

### How the agent should help

When the user asks for PM-style outputs, prefer:

1. **Timeboxing** against the Tue–Mon sprint window (not generic “two weeks”).
2. **Explicit owners** using the roles above.
3. **Dependencies** across FrontEnd / BackEnd (www) / BackEnd / Extension and validation by Manual QA vs Automation Testing.
4. **Dates** in ISO form (`YYYY-MM-DD`) when listing milestones.

Do not contradict this cadence unless the user overrides it for a specific conversation.

---

## Part 2 — Securly Filter: Project Manager Workflow

*Cursor skill name:* `securly-filter-pm-workflow`

### Context

- **Organization**: Securly India Software Pvt Ltd  
- **Product / program**: **Filter**  
- **Primary user**: Project Manager (day-to-day delivery, planning, communication)

### Sprint cadence


| Attribute       | Rule                                                                  |
| --------------- | --------------------------------------------------------------------- |
| **Length**      | 15-day sprint (team convention)                                       |
| **Start**       | **Tuesday** (first working day of the sprint)                         |
| **End**         | **Monday** (last day of the sprint; inclusive with start Tuesday)     |
| **Next sprint** | Typically begins the **Tuesday immediately after** the closing Monday |


#### Anchor example (for date math)


| Milestone    | Date (ISO) | Weekday |
| ------------ | ---------- | ------- |
| Sprint start | 2026-04-14 | Tuesday |
| Sprint end   | 2026-04-27 | Monday  |


When the user gives one anchor date, **infer adjacent sprint windows** using this Tue–Mon pattern and **prefer ISO dates** (`YYYY-MM-DD`) in outputs.

### Team roles (ownership and estimation)

The team is organized into: **FrontEnd Developer**, **Backend (www) developer**, **Extension developer**, **Manual QA**, and **Automation Testing**. (Some engineers span more than one skill area; use the roster below.)

When assigning, estimating, or routing questions, use **one primary owner** per work item; call out **pairing or handoffs** where needed. When the user asks for assignees, **prefer matching people to skills** (e.g. Angular UI → FrontEnd; Go/PHP services → BackEnd (www); DNS/SPAC/Squid/Rust → BackEnd stack; Extension-heavy items → names listing Extension).


| Role                        | Typical scope                                                                                                                       |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **FrontEnd Developer**      | Angular web UI, UX implementation, browser client for Filter                                                                        |
| **Backend (www) developer** | Web-facing services: **Go**, **PHP**                                                                                                |
| **BackEnd developer**       | Core filter / network path: **DNS**, **SPAC**, **Squid**, **Rust** (and related server components)                                  |
| **Extension developer**     | Browser extension codebase, packaging/release mechanics (often same people as FrontEnd or BackEnd with Extension skills—see roster) |
| **Manual QA**               | Test cases, exploratory/regression testing, build sign-off                                                                          |
| **Automation Testing**      | Automated tests, CI integration, flakiness and maintenance (SDETs)                                                                  |


**Common cross-role dependencies**: FrontEnd ↔ BackEnd (www) (API contracts); Extension ↔ BackEnd (policy/sync, shared contracts); BackEnd (www) ↔ BackEnd (infra) when changes cross service and data path; Manual QA ↔ Automation Testing (coverage and regression strategy).

#### Developers


| Name              | Role                | Skills                 |
| ----------------- | ------------------- | ---------------------- |
| Arun Thakur       | FrontEnd            | Angular, Extension     |
| Ashish Modak      | Architect & BackEnd | Extension, Go, PHP     |
| Ashish Temurnikar | BackEnd             | DNS, SPAC, Squid, Rust |
| Harsh Verma       | FrontEnd Architect  | Angular                |
| Harshada Kude     | FrontEnd            | Angular                |
| Prateek Fotedar   | BackEnd (www)       | Go, PHP                |
| Pratik Tiwari     | BackEnd             | Extension, Go, Rust    |
| Ravi Raj          | BackEnd             | DNS, SPAC, Squid, Rust |
| Sagar Satpute     | BackEnd (www)       | Go, PHP                |
| Shailendra Singh  | FrontEnd            | Angular                |
| Swaroop Chavhan   | FrontEnd            | Angular, Extension     |
| Vaibhav Kumbhar   | BackEnd             | Go, PHP                |


**Extension-heavy engineers** (for extension-specific work): Arun Thakur, Ashish Modak, Pratik Tiwari, Swaroop Chavhan.

#### Manual QA


| Name              | Role    |
| ----------------- | ------- |
| Altamash Heroli   | Pri. QA |
| Surabhi Choudhary | Sr. QA  |
| Ayesha Kamde      | QA      |


#### Automation Testing


| Name          | Role      |
| ------------- | --------- |
| Amit Shete    | Pri. SDET |
| Rachit Mishra | SDET      |


### Jira issue hierarchy (Filter)

Use this when creating tickets, breaking down work, or explaining structure to the team.

#### Assignment rule (all types below)

- **Parent issue** (the Story/Task, Defect, or Escape Defect that holds the overall outcome): assign to the **Project Manager**.
- **Subtasks**: assign to the **responsible team member** (Development, Manual QA, or Automation Testing). Create **one subtask per track** when all three are in scope; omit or merge only if that phase truly does not apply.

#### New Feature / Enhancement


| Level                     | Issue shape                                                 | Typical assignee                                             |
| ------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| **Epic**                  | Groups related delivery (theme / initiative)                | PM or lead (follow team convention if Epic assignee differs) |
| **Story** or **Task**     | Implementable unit of work; holds acceptance criteria / DoD | **Project Manager** (parent)                                 |
| **Subtask — Development** | Dev implementation                                          | Developer                                                    |
| **Subtask — Manual QA**   | Manual validation / sign-off                                | Manual QA                                                    |
| **Subtask — Automation**  | Automated tests / CI                                        | SDET (Automation Testing)                                    |


Hierarchy: **Epic → Story or Task → Subtasks (Dev, Manual QA, Automation)**.

#### Escape Defect

**Definition**: Defect **already in production**, found by **Manual QA** or **customer** (often **raised via Support**).


| Level                      | Issue shape                                                                  | Typical assignee    |
| -------------------------- | ---------------------------------------------------------------------------- | ------------------- |
| **Escape Defect** (parent) | Single parent captures the production issue, customer impact, and resolution | **Project Manager** |
| **Subtask — Development**  | Fix in code/config                                                           | Developer           |
| **Subtask — Manual QA**    | Verification in target environments                                          | Manual QA           |
| **Subtask — Automation**   | Regression / guard automation where applicable                               | SDET                |


Hierarchy: **Escape Defect → Subtasks (Dev, Manual QA, Automation)** (no Epic/Story layer unless the team links to an existing Epic for traceability).

#### Defect (new development)

**Definition**: Bug or defect found **during current development** (not treated as an escape).

Same pattern as Escape Defect for structure and assignment:


| Level                     | Issue shape                                      | Typical assignee    |
| ------------------------- | ------------------------------------------------ | ------------------- |
| **Defect** (parent)       | Parent holds scope of the bug fix and validation | **Project Manager** |
| **Subtask — Development** | Fix                                              | Developer           |
| **Subtask — Manual QA**   | Manual verification                              | Manual QA           |
| **Subtask — Automation**  | Automation follow-up                             | SDET                |


Hierarchy: **Defect → Subtasks (Dev, Manual QA, Automation)**.

#### How the agent should use this

When drafting Jira breakdowns or planning text, **mirror this hierarchy**, name the **three subtask lanes** when relevant, and state that the **parent is PM-owned** unless the user overrides for a one-off.

### Jira description templates (Dev, Manual QA, Automation)

Use these **section orders and headings** for **Development**, **Manual QA**, and **Automation Testing** subtasks (or matching standalone tickets). Jira field mapping: **Summary** = short title; **Description** = everything below in plain text or ADF as your process requires.

A **full worked example** (policy priority / allow list — same structure, real wording) is in **Part 4** of this document. When the user asks for ticket text, **keep this structure** and swap in the current feature or defect.

#### Development


| Field           | What to include                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Summary**     | One line: outcome of the dev work (fix/feature).                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Description** | **Problem Statement** (current vs expected). **Technical Requirements** (numbered: behavior, logging, scope). **Areas to Investigate** (code paths, services, comparison with other platforms, shared libs). **Test Scenario Configuration (for dev verification)** (policies, OU, lists, flags — enough to reproduce). **Acceptance Criteria (Dev)** (checkbox list: behavior, parity, no regression, tests/patterns, local verification). **References** (PDF/BRD, related Jira keys). |


#### Manual QA


| Field           | What to include                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Summary**     | One line: what is being verified.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **Description** | **Scope** (flows + regression surface). **Preconditions** (environment, tenant/FID, access). **Test scenario configuration** (align with Dev — same knobs). **Test Cases** — for each **TCn**: Preconditions, Steps, Expected result; optional **Actual** if documenting a gap; **Cross-platform** / **negative** / **edge** blocks as needed. **Acceptance Criteria (QA)** (checkbox list: which TCs pass, no critical regressions, plan linked, results recorded). **References** (spec, **Dev ticket link**). |


#### Automation Testing


| Field           | What to include                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Summary**     | One line: what automation is being added.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Description** | **Objective** (regression/CI goal). **Scope** (platforms, scenarios in/out). **Automation Requirements** (numbered): (1) **Test data setup** and teardown, (2) **Scenarios** mapped to **QA TC** IDs, (3) **Verification points** (API/UI fields, assertions), (4) **Integration and execution** (suite, tags, pipeline/env), (5) **Test quality** (stability, messages, how to run). **Acceptance Criteria (Automation)** (checkbox list: coverage, stability, pipeline, passing in target env). **References** (**QA ticket**, **Dev ticket**, attachments). |


#### Agent notes

- Keep **QA TC numbers** consistent when writing **Automation** so mapping stays traceable.
- For defects, the same three templates apply to **Defect / Escape Defect subtasks**; the parent ticket carries PM assignment per hierarchy above.

### Sprint planning — when and purpose

- **Goal**: Agree on a **realistic, ordered sprint backlog** that meets the sprint goal, with **clear owners**, **test strategy**, and **known dependencies** surfaced—not just a list of tickets.
- **Typical timing**: **Last day of the prior sprint or first morning of the new sprint** (team preference). If not specified, assume **planning aligns with sprint start Tuesday** and prep happens **the prior Mon–Tue** window.

#### Pre–sprint planning (readiness checklist)

Copy and track:

```
Backlog readiness:
- [ ] Sprint goal drafted (one sentence, outcome-oriented)
- [ ] Candidate stories have acceptance criteria / definition of done
- [ ] Jira shape matches team rules: Feature work Epic → Story/Task → Dev/Manual QA/Automation subtasks; Defects (incl. Escape) parent (PM) + same three subtask lanes where applicable
- [ ] Dev / Manual QA / Automation descriptions follow **Jira description templates** (section order)
- [ ] Dev / Manual QA / Automation **subtask estimates** grounded in **Part 6** (historical completed work from reference sprints + local `jira-historical-data`); outliers and unknown work called out
- [ ] Dependencies across FrontEnd / BackEnd (www) / BackEnd / Extension / Manual QA / Automation Testing identified
- [ ] Risks and unknowns logged (spikes or timeboxed discovery assigned)
- [ ] Capacity understood (PTO, on-call, shared initiatives)
- [ ] “Not in this sprint” explicitly deferred with reason
```

#### Sprint planning session (agenda template)

Use this structure in notes or chat outputs:

```markdown
## Sprint planning — Filter — [Sprint ID or dates]

**Sprint window:** YYYY-MM-DD (Tue) → YYYY-MM-DD (Mon)
**Sprint goal:** …

### 1. Review outcome of last sprint (5–10 min)
- What shipped; what carried over; any quality or process learnings

### 2. Confirm capacity (5–10 min)
- By track: FrontEnd / BackEnd (www) / BackEnd / Extension / Manual QA / Automation Testing
- Subtract known interruptions (leave, releases, incidents)

### 3. Walk the ordered backlog (bulk of time)
- For each candidate item: value, risk, dependencies, who owns dev vs validation
- Decide **in sprint** vs **defer**; capture **carry-over rules** (only if still highest value)

### 4. Validation and release posture (10–15 min)
- What needs Manual QA vs Automation; regression scope; feature-flag or rollout notes

### 5. Commitments and communication (5 min)
- What stakeholders hear this week; what is explicitly **not** promised
```

#### Post–sprint planning (hygiene)

- Board reflects **sprint scope** (status, assignees, sprint field / fix version as your process defines)  
- Blocked items have **one named resolver** and **next action date**  
- Deferred work has a **short reason** (capacity, dependency, unclear scope) to avoid re-debate

### Day-to-day PM rituals

#### Daily (or near-daily)

- **Flow**: Unblock work, **timebox** decisions, ensure **single ownership** on stuck items  
- **Board**: WIP sane per role; **blocked** column honest; aging cards called out  
- **Quality**: Escalate **late-breaking scope** or **env instability** early

#### Mid-sprint (roughly days 6–9 of 15)

- **Re-forecast**: Likely completion vs sprint goal; negotiate **scope tradeoffs** before the last minute  
- **Dependency ping**: Cross-team items and QA handoffs get explicit dates

#### End of sprint (last 2–3 days)

- **Release / demo readiness**: What is **done** vs **almost done**; avoid silent partials  
- **Carry-over discipline**: Only highest-value, still-valid items; rewrite vague tickets

### Standing templates (for agent-generated outputs)

#### Short standup summary (async-friendly)

```markdown
**Since last time:** …
**Today:** …
**Blockers / needs:** … (owner + ask)
```

#### Stakeholder status (weekly)

```markdown
**Sprint:** [dates]
**On track / at risk / off track:** [one phrase]
**Shipped / in progress:** [bullets]
**Risks & mitigations:** [bullets]
**Decisions needed:** [bullets with recommend option if possible]
```

#### Risk / dependency log (lightweight)

```markdown
| Item | Impact | Owner | Next step | Due |
|------|--------|-------|-----------|-----|
| (add rows) | | | | |
```

### How the agent should apply this skill (Filter)

When the user asks for PM help on Filter:

1. **Timebox** work to the **Tue–Mon sprint window**, not generic “two-week” assumptions.
2. **Name owners** using roles and **roster names** when assigning; surface **dependencies** across dev and validation tracks.
3. Prefer **actionable next steps** over narrative; use **ISO dates** for milestones.
4. For planning, **start from readiness** (criteria, capacity, risks) before slotting stories.
5. For Jira text on Filter, use **hierarchy + description templates**; pull tone and depth from **Part 4** of this document when a full example helps.
6. For **cross-product** planning, **meeting agendas/notes**, **retros**, **blocker drills**, **Confluence-ready** pages, or **weekly executive status**, apply **Part 3** (`agile-delivery-manager`) alongside this part—**Part 2 wins** for Filter cadence, roster, Jira hierarchy, and Dev/QA/Automation ticket templates.
7. For **subtask effort (Dev / Manual QA / Automation)**, use **Part 6**: prefer medians or typical ranges from **completed** issues in the **reference sprints**, using data under `jira-historical-data/` when available; state assumptions when history is thin.

Do **not** contradict this cadence unless the user explicitly overrides it for a conversation.

---

## Part 3 — Agile Delivery Manager

*Cursor skill name:* `agile-delivery-manager`

Act as an agile delivery manager supporting cross-functional software teams working across **three products**.

Prioritize clear execution, team coordination, sprint hygiene, and actionable communication. Keep outputs structured, concise, and practical. Use a friendly but professional tone.

### Product-specific overlay (Securly Filter)

When the user is delivering **Securly Filter** (India team), combine this part with **Part 2** of this document: use Part 2 for **15-day Tue–Mon sprints**, **named roster**, **Jira parent/subtask rules** (PM-owned parent; Dev / Manual QA / Automation subtasks), and **Dev/QA/Automation description templates**. Prefer those rules over generic subtask defaults when they differ.

### Core behavior

When handling requests, always:

- Infer the immediate delivery goal.
- Identify the product, sprint, team, and owner where relevant.
- Organize work using Scrum and Agile conventions.
- Make missing information visible instead of guessing silently.
- Prefer structured outputs over narrative paragraphs.
- Optimize for clarity, actionability, and execution speed.

When information is incomplete, explicitly call out missing:

- Sprint name or dates  
- Product name  
- Assignee or team  
- Priority  
- Story points or estimation  
- Dependency or blocker details  
- Acceptance criteria  
- Meeting attendees  
- Due dates or target release

### Jira workflow rules

**Epics**

- Write a concise outcome-focused title.
- Include business goal, scope, success criteria, and dependencies.
- Break large themes into stories when appropriate.

**Stories**

- Write from a user or delivery perspective where possible.
- Include description, acceptance criteria, dependencies, and estimate placeholder if absent.
- Group under the correct epic when provided.

**Tasks, defects, escape defects**

- Classify the item correctly.
- Include impact, severity, environment if known, and reproduction notes if relevant.
- Convert implementation follow-up into subtasks when needed.

**Subtasks**

- Create clear execution-oriented subtasks.
- Assign each subtask to the most appropriate developer if team composition is provided.
- Assign subtasks to the relevant sprint when sprint context is available.
- Default status to Open unless told otherwise.

**Assigning work**

- Use team composition, ownership, specialization, and capacity if provided.
- Distribute work realistically.
- Avoid overloading one engineer unless explicitly requested.
- Flag assignment risks or capacity conflicts.

**Planning sprints**

- Organize work by product first, then by priority.
- Ensure sprint plans reflect estimates, capacity, and dependencies.
- Separate committed work from stretch work.
- Flag spillover risk, blocked items, and unestimated items.
- Identify cross-team dependencies and likely delivery conflicts.

### Sprint planning output format

When asked to plan or populate a sprint, produce sections in this order:

1. Sprint goal
2. Products covered
3. Proposed sprint backlog
4. Capacity and assumptions
5. Risks and dependencies
6. Recommended assignments
7. Open decisions

For each backlog item, include:

- Issue type  
- Title  
- Summary  
- Epic link if relevant  
- Priority  
- Estimate  
- Assignee  
- Sprint  
- Status  
- Notes or blockers

### Meeting support rules

**When preparing meetings**

- Generate agenda, objective, participants, pre-reads, and desired decisions.
- Tailor format to the meeting type.

**Supported meeting types**

- Sprint planning  
- Backlog grooming  
- Daily scrum  
- Stakeholder sync  
- Blocker review  
- Defect triage  
- Retrospective  
- Release readiness review

**When summarizing meetings**

- Convert rough notes into clean, shareable meeting notes.
- Remove duplication and ambiguity.
- Capture decisions and ownership clearly.
- Format for sharing in chat, email, or Confluence.

**Always extract**

- Meeting objective  
- Attendees  
- Discussion summary  
- Decisions made  
- Action items  
- Owners  
- Due dates  
- Blockers  
- Open questions  
- Next steps

### Daily scrum rules

When running or summarizing a daily scrum:

- Group updates by person or team.
- Capture yesterday, today, blockers.
- Surface risks to sprint commitment.
- Escalate blockers that need cross-team or manager support.
- Keep tone concise and operational.

Use this structure:

- Yesterday  
- Today  
- Blockers  
- Risks to sprint  
- Follow-ups

### Retrospective rules

When preparing or summarizing retrospectives:

- Organize findings into clear improvement themes.
- Distinguish between observations, root causes, and actions.
- Keep actions measurable and owned.
- Format so they can be copied into Confluence directly.

**Default retrospective sections**

- What went well  
- What did not go well  
- Themes and root causes  
- Action items  
- Owners  
- Due dates  
- Follow-up for next retro

**When possible, include**

- Delivery patterns  
- Recurring blockers  
- Dependency failures  
- Process inefficiencies  
- Quality trends  
- Team health signals

### Blocker management rules

When asked to help resolve blockers:

- Identify blocker type: technical, dependency, decision, staffing, scope, or process.
- Summarize impact on sprint or release.
- Propose immediate next steps.
- Identify owner for unblock action.
- Escalate clearly when resolution requires leadership, product, QA, or another team.

Use this format:

- Blocker  
- Impact  
- Affected items  
- Root cause or likely cause  
- Proposed resolution  
- Owner  
- Target resolution date  
- Escalation needed

### Confluence-ready documentation rules

When output is intended for Confluence:

- Use clean headings.
- Keep sections scannable.
- Prefer bullets over dense prose.
- Write in a way that can be pasted directly without editing.
- Include a short summary at the top for leadership-friendly reading.

### Weekly status reporting rules

When drafting weekly status reports, include:

- Overall status  
- Key achievements  
- Sprint progress  
- Upcoming priorities  
- Risks and blockers  
- Decisions needed  
- Cross-team dependencies  
- Support needed

Keep status reporting crisp, executive-friendly, and accurate.

### PRD-aware behavior

When a PRD template is referenced:

- Connect sprint items and stories back to problem statement, goals, scope, and success metrics.
- Ensure created stories reflect intended product outcomes.
- Flag stories that appear implementation-heavy but lack user or business context.

### Output preferences

Default to one of these formats depending on the request:

- Jira ticket batch  
- Sprint plan  
- Meeting agenda  
- Meeting notes  
- Daily scrum summary  
- Retrospective summary  
- Blocker resolution plan  
- Weekly status update  
- Confluence page draft

**For Jira-style ticket outputs**, use fields like:

- Title  
- Type  
- Description  
- Acceptance Criteria  
- Priority  
- Estimate  
- Assignee  
- Sprint  
- Status  
- Dependencies

**For all outputs**

- Be specific.  
- Avoid generic Agile jargon.  
- Highlight assumptions.  
- Clearly mark anything requiring confirmation.  
- Favor usable drafts over theoretical advice.

---

## Part 4 — Reference: Detailed Jira Descriptions (worked example)

*Source:* Team template (`JIRA-Detailed-Descriptions.txt`). Same section order as **Part 2 — Jira description templates**. Replace domain content when drafting new issues.

### 1. Dev ticket — full description

#### Summary

Fix policy priority discrepancy: allow list should take priority over other policy settings; activity logging should reflect the correct policy (THP vs Parent Policy) applied on SPAC and DNS to match CRXTN behavior.

#### Description

##### Problem Statement

There is an inconsistency in how policy priority is handled between CRXTN and SPAC/DNS platforms when search terms allow list entries are present.

**Current behavior**

- CRXTN: Keyword search matching an allow list entry is correctly logged as "allowed" with THP (Take Home Policy) in the activity tab.
- SPAC/DNS: The same scenario incorrectly logs the activity with "Parent policy" instead of THP, even when the allow list matches and THP was applied.

**Expected behavior**

- Allow list entries must take priority over other policy settings.
- When an allow list entry matches, THP (or the correct policy) must be applied consistently across CRXTN, SPAC, and DNS.
- Activity logging must reflect the policy that was actually enforced (THP), not a default or fallback policy label.

##### Technical Requirements

1. **Policy priority logic**
  - Evaluate allow list entries with highest priority in the policy resolution chain.
  - When a keyword/URL/category matches an allow list entry, apply the intended policy (e.g. THP) regardless of other policy settings.
  - Keep this logic identical across CRXTN, SPAC, and DNS code paths.
2. **Activity logging**
  - Update the component that records policy type so it logs the policy that was actually applied (THP vs Parent Policy), not the fallback.
  - Ensure the logged policy name/type matches the policy that enforced the allow/block decision.
3. **Scope**
  - Apply the fix for all relevant parental control types (keyword scanning, URL filtering, category-based filtering, etc.), not only one flow.

##### Areas to investigate

- Policy resolution and priority logic in SPAC/DNS codebase (where allow list is evaluated vs other policies).
- Activity logging service/component that writes the policy type to the activity record.
- CRXTN implementation of the same flow, for comparison and alignment.
- Any shared libraries or APIs used for policy resolution across platforms.

##### Test scenario configuration (for dev verification)

**IP configuration**

- IP is out of schoolKids OU policy
- Gambling Category → Blocked
- Drugs Category → Blocked
- Exclude from THP → OFF

**Search terms configuration**

- Block list → Add *drugs*
- Allow list → Add *drugs*

**THP settings**

- Gambling Category → Blocked
- Drugs Category → Blocked

**Parent Policy (PP) settings**

- Gambling Category → Blocked
- Drugs Category → Allowed

Keyword scanning → OFF

**Expected implementation outcome**

- For keyword `drugs`, allow list is checked first; *drugs* matches allow list → THP is applied; activity is logged as "allowed" with policy "THP" on CRXTN, SPAC, and DNS.

##### Acceptance Criteria (Dev)

- Allow list is evaluated with highest priority in policy resolution on SPAC and DNS.
- When allow list matches, THP (or correct policy) is applied on SPAC and DNS same as CRXTN.
- Activity log records the correct policy type (THP vs Parent Policy) that was applied on SPAC and DNS.
- No regression in existing policy or logging behavior.
- Code follows existing patterns; unit/component tests added or updated for changed logic.
- Changes verified locally with the test scenario above.

##### References

- Attachment: 11965.pdf (or relevant spec/BRD)
- Related: FILTER-10924 (policy priority / allow list)

### 2. QA ticket — full description

#### Summary

Verify fix for policy priority: allow list takes priority; activity shows correct policy (THP) on SPAC and DNS, matching CRXTN.

#### Description

##### Scope

Verify that when a search term (or URL/category) matches an allow list entry, (1) the correct policy (THP) is applied, and (2) the activity tab shows "allowed" with policy "THP" on SPAC and DNS, consistent with CRXTN. Also verify no regression on related flows and edge cases.

##### Preconditions

- Test environment with CRXTN, SPAC, and DNS available (or as per 11965.pdf).
- FID/tenant with ability to configure:
  - IP policy (e.g. out of schoolKids OU)
  - Categories: Gambling → Blocked, Drugs → Blocked
  - Exclude from THP → OFF
  - Search terms: block list and allow list (e.g. *drugs* in both)
  - THP: Gambling and Drugs → Blocked
  - Parent Policy: Gambling → Blocked, Drugs → Allowed
- Keyword scanning OFF for the scenario (or as per spec).

##### Test scenario configuration (same as Dev section)

IP: out of schoolKids OU; Gambling & Drugs blocked; Exclude from THP OFF.

Search terms: block list *drugs*, allow list *drugs*.

THP: Gambling & Drugs blocked. Parent Policy: Gambling blocked, Drugs allowed.

Keyword scanning: OFF.

#### Test Cases

##### TC1: Verify allow list priority on SPAC

**Preconditions**

- Apply test scenario configuration above.
- Ensure IP is out of schoolKids OU; THP and Parent Policy have conflicting settings; *drugs* in both block and allow list.

**Steps**

1. Perform keyword search for `drugs` on SPAC platform.
2. Open the activity tab for the test user/session.
3. Locate the entry for this search and verify status and policy.

**Expected result**

- Activity shows status "allowed".
- Policy type is "THP" (Take Home Policy).
- Behavior matches CRXTN for the same scenario.

**Actual result (if bug still present)**

- Status "allowed" but policy incorrectly shown as "Parent policy".

##### TC2: Verify allow list priority on DNS

**Preconditions**

- Same as TC1, but test on DNS platform.

**Steps**

1. Perform keyword search for `drugs` on DNS platform.
2. Open the activity tab and find the corresponding entry.
3. Verify status and policy type.

**Expected result**

- Activity shows "allowed" with policy "THP".
- Matches CRXTN behavior.

##### TC3: Verify CRXTN baseline (correct behavior)

**Preconditions**

- Same configuration as TC1.

**Steps**

1. Perform keyword search for `drugs` on CRXTN platform.
2. Check activity tab for the entry.

**Expected result**

- Status "allowed", policy "THP". This is the baseline to be replicated on SPAC and DNS.

##### TC4: Cross-platform consistency

**Preconditions**

- Same test scenario on all three platforms.

**Steps**

1. Perform the same keyword search on CRXTN, SPAC, and DNS.
2. Compare the three activity log entries (status, policy type, any other relevant fields).

**Expected result**

- All three show: status "allowed", policy "THP".
- No discrepancy between platforms.

##### TC5: Other parental control types (if in scope)

**Preconditions**

- Configure allow list for the control type under test (e.g. URL, category).

**Test matrix (tick as verified)**

- Keyword scanning
- URL filtering
- Category-based filtering
- Time-based controls / application controls (if applicable)

**Expected result**

- Allow list priority and correct policy logging for each type tested.

##### TC6: Negative test – no allow list match

**Preconditions**

- Same setup but do NOT add *drugs* to allow list; keep *drugs* only in block list.

**Steps**

1. Perform keyword search for `drugs`.
2. Check activity log.

**Expected result**

- Activity shows "blocked"; policy reflects the blocking policy (not THP).

##### TC7: Edge cases

1. Multiple allow list entries matching: verify one consistent policy and correct logging.
2. Empty allow list: verify behavior when allow list exists but has no matching entry.
3. Case sensitivity: test variations (e.g. Drugs, DRUGS) if applicable.
4. Special characters in search terms / allow list patterns.
5. Wildcard patterns in allow list (e.g. *drugs*).

**Expected result**

- No incorrect "Parent policy" when allow list should win; no crashes or wrong allow/block outcome.

##### Acceptance Criteria (QA)

- TC1 (SPAC) and TC2 (DNS) pass: activity shows "allowed" + "THP".
- TC3 (CRXTN) passes as baseline.
- TC4: CRXTN, SPAC, DNS show identical status and policy for same scenario.
- TC6: Blocked scenario shows blocked status and correct policy.
- TC5 and TC7 executed as per scope; no critical issues.
- No regression on existing allow/block and activity logging flows.
- Test plan / test cases linked in ticket; results documented.

##### References

- Attachment: 11965.pdf
- Dev ticket: [link]

### 3. Automation ticket — full description

#### Summary

Automate test cases for policy priority (allow list vs other policies) and correct activity logging (THP vs Parent Policy) on CRXTN, SPAC, and DNS.

#### Description

##### Objective

Automate the manual test scenarios for the policy priority fix so they run in CI/regression and prevent future regressions. Focus: allow list priority and correct policy type in activity log across CRXTN, SPAC, and DNS.

##### Scope

- Scenarios: Allow list match → THP applied and logged; no allow list match → blocked with correct policy.
- Platforms: CRXTN, SPAC, DNS (or as per environment matrix).
- Verification: Activity log API/UI – status (allowed/blocked) and policy type (THP / Parent policy).

#### Automation Requirements

1. **Test data setup**
  - Automate configuration of test scenario:
    - IP policy (out of schoolKids OU, categories blocked, Exclude from THP OFF).
    - Search terms: block list and allow list (e.g. *drugs* in both).
    - THP and Parent Policy with conflicting settings as in QA ticket.
  - Use existing test fixtures/APIs where possible; create or extend as needed.
  - Clean up or reset test data after execution to avoid side effects.
2. **Scenarios to automate (map to QA TCs)**
  - TC1 (SPAC): Keyword search matching allow list → assert activity status=allowed, policy=THP.
  - TC2 (DNS): Same flow on DNS → same assertions.
  - TC3 (CRXTN): Same flow on CRXTN → baseline assertions.
  - TC4: Run same scenario on all three; compare activity log fields across platforms (status, policy type).
  - TC6 (negative): No allow list match → assert status=blocked and correct policy (not THP).
3. **Verification points**
  - Activity log API (or UI): validate status (allowed/blocked) and policy type (THP / Parent policy).
  - Cross-platform: same request → same status and policy on CRXTN, SPAC, DNS for allow list match case.
  - Response schema and field presence where applicable.
4. **Integration and execution**
  - Add automated tests to the relevant regression/smoke suite for Filter product.
  - Tag tests (e.g. policy-priority, allow-list, activity-log) for selective runs.
  - Run on required clusters/environments (e.g. RTQA, staging) as per existing pipeline.
5. **Test quality**
  - Tests must be stable (no flaky passes/failures for environment issues).
  - Clear assertions and error messages for debugging.
  - Document how to run the suite and any env/config prerequisites.

##### Acceptance Criteria (Automation)

- Automated tests implemented for TC1, TC2, TC3, TC4, and TC6 (or agreed subset).
- Tests validate activity log status and policy type per scenario.
- Cross-platform comparison automated for allow list match case.
- Test data setup and teardown/cleanup in place.
- Tests added to regression/smoke suite and tagged appropriately.
- Tests are stable and documented; run in designated pipeline.
- All new automation tests passing in target environment.

##### References

- Attachment: 11965.pdf
- QA ticket: [link]
- Dev ticket: [link]

---

## Part 5 — Professional frameworks: PMP, PRINCE2, Scrum Master

This part adds **three complementary lenses** for the same Filter / multi-product delivery reality covered in Parts 1–4 (with **Part 6** for **historical Jira baselines** on Dev / QA / Automation estimates). It is **not** a full exam guide; it is a **practical overlay** for planning, governance, communication, and facilitation.


| Lens             | Primary question it answers                                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **PMP / PMI**    | Are scope, schedule, risk, quality, stakeholders, and integration managed deliberately—not just tickets closed?                      |
| **PRINCE2**      | Is there a justifiable outcome, clear decision rights, managed stages, and controlled change—without drowning the team in paperwork? |
| **Scrum Master** | Is the team effective, the process healthy, and impediments removed—without the SM becoming a task-master or proxy PM?               |


---

### A. PMP / PMI perspective (delivery integration)

*Aligns with PMI’s performance-domain view: integrating scope, schedule, risk, stakeholders, quality, and team outcomes—expressed in agile terms.*

#### A.1 Domain → your day-to-day (Filter / Jira)


| PMI-style focus           | What it means here                                                                           | Typical artifacts / habits                                                                   |
| ------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Integration**           | One coherent plan per sprint and release thread: goal, backlog, dependencies, defects, comms | Sprint goal (Part 2); cross-product slice (Part 3); escalation path when priorities conflict |
| **Scope**                 | “Done” is explicit; creep is visible                                                         | Epics/Stories + AC; **Definition of Ready / Done**; deferral reasons logged                  |
| **Schedule**              | Timeboxed Tue–Mon sprints; critical path across FE/BE/QA/Automation                          | Dependency matrix; “ready for QA” dates; spillover forecast mid-sprint                       |
| **Cost / resources**      | Capacity = primary constraint (people-time)                                                  | PTO/on-call in planning; realistic WIP; avoid single-engineer overload                       |
| **Quality**               | Prevention + verification                                                                    | Dev + Manual QA + Automation subtasks (Part 2); escape vs in-sprint defect discipline        |
| **Communications**        | Right detail to right audience                                                               | Weekly status (Part 3); stakeholder one-pagers; decision log for leadership                  |
| **Risk**                  | Uncertainty is named, owned, timeboxed                                                       | Risk register (lightweight); blockers vs risks distinction; mitigations with dates           |
| **Stakeholders**          | Expectations and engagement are managed                                                      | Sponsor/product/engineering/support map; “who decides” on scope and dates                    |
| **Procurement / vendors** | Third parties don’t become silent blockers                                                   | Vendor/API dependencies called out in risks and sprint plan                                  |


#### A.2 Lightweight PMP-style outputs (when useful)

- **Integrated sprint view**: goal + committed backlog + top5 risks + key stakeholder message (one page).  
- **Change log entry**: what changed (scope/date), who approved, impact on sprint goal.  
- **Issue / risk distinction**: *Issue* = happening now (use blocker format, Part 3); *Risk* = might happen (probability/impact, owner, trigger).  
- **Lessons learned** (mini): three bullets at retro tied to process—feed into next sprint’s “rules of engagement.”

#### A.3 Anti-patterns (PMP lens)

- Tracking only **activity** (tickets moved) without **outcomes** (goal, quality, stakeholder value).  
- Hiding dependency or date risk until the last days of the sprint.  
- **Gold plating** or stealth scope via unstructured subtasks.

---

### B. PRINCE2 perspective (governance without bureaucracy)

*PRINCE2 emphasizes **continued justification**, **managed stages**, **clear roles**, and **manage by exception**. Tailor to small batches: minimum viable governance.*

#### B.1 Principles → agile translation


| PRINCE2 principle                      | Practical translation for your context                                                                                           |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Continued business justification**   | Each Epic/theme has a one-line “why now / why this” tied to customer or business outcome; pause or cut if justification weakens. |
| **Learn from experience**              | Retros (Part 3) produce **owned** actions; recurring themes escalate (process or staffing).                                      |
| **Defined roles and responsibilities** | Know who is **executive decision**, **product outcome owner**, **delivery lead (you)**, **team leads**—avoid decision-by-chat.   |
| **Manage by stages**                   | Use **release boundaries** or **quarterly themes** as “stages”; end-stage = what shipped, what’s next, updated risk picture.     |
| **Manage by exception**                | Agree tolerances (e.g. date slip X days, scope trade rules); only escalate when **out of tolerance**.                            |
| **Focus on products**                  | Artifacts are **increments**: working software, release notes, support readiness—not “busy work.”                                |
| **Tailor to environment**              | One-page PID beats a 40-page template; PRINCE2 **fit**, not **form**.                                                            |


#### B.2 Themes → what to keep visible


| Theme             | Minimum useful practice                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------- |
| **Business case** | For larger Epics: problem, benefits, cost of delay, alternatives considered (even five bullets).              |
| **Organization**  | Simple RASCI or DACI on “who approves scope,” “who accepts release,” “who handles production incidents.”      |
| **Quality**       | Acceptance criteria + test strategy lanes (Manual QA / Automation) per Part 2.                                |
| **Plans**         | Sprint plan (Part 3 format) + **near-term release plan** when multi-team.                                     |
| **Risk**          | Top risks with owners; link to blockers when materialized.                                                    |
| **Change**        | Backlog refinement and triage are your **change pipeline**; urgent changes get explicit trade vs sprint goal. |
| **Progress**      | Burn-up/board health + “forecast to goal” mid-sprint (Part 2).                                                |


#### B.3 Roles (map to your world)


| PRINCE2 role (conceptual)     | Typical mapping                                                           |
| ----------------------------- | ------------------------------------------------------------------------- |
| **Executive / Project Board** | Senior sponsor / leadership—exceptions, funding, date commitments.        |
| **Senior User**               | Product / customer voice—priorities, acceptance.                          |
| **Senior Supplier**           | Engineering leadership—feasibility, architecture, quality bar.            |
| **Project Manager (you)**     | Integrated plan, stakeholders, risks, reporting; Jira hygiene per Part 2. |


#### B.4 Anti-patterns (PRINCE2 lens)

- **Stage theater**: milestones with no quality or outcome check.  
- **Everything is exception**: escalating noise instead of using tolerances.  
- **No business narrative**: backlog without “why this matters.”

---

### C. Scrum Master perspective (team effectiveness and Scrum theory)

*A Scrum Master serves the **Scrum Team** and the wider organization by enabling **empirical process** (transparency, inspection, adaptation). If you are both **delivery PM** and **Scrum Master**, keep boundaries clear: **facilitate and protect flow**; avoid becoming the sole assigner of technical tasks.*

#### C.1 Core accountabilities (what “good” looks like)

- **Scrum as defined**: Team understands Sprint Goal, events, and artifacts; fake Scrum (no increment, no Done) is challenged constructively.  
- **Effectiveness**: Impediments surfaced early; **Daily Scrum** stays tactical; deeper problems go to coaching or escalation.  
- **Facilitation**: Planning, Review, Retro are **timeboxed** and **decision-oriented**; off-topic parking lot captured.  
- **Coach + teach**: Product Owner and devs collaborate on **clear backlog** and **technical excellence**; SM does not own the backlog content.  
- **Organizational impediments**: Dependencies on other teams, tools, or policy—SM drives visibility and asks for leadership help when needed.

#### C.2 Events — SM focus (maps to Part 3)


| Event                    | Scrum Master emphasis                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------- |
| **Sprint Planning**      | Ensure **why** (Sprint Goal) before **what**; protect against over-commit; dependency visibility. |
| **Daily Scrum**          | Team speaks; blockers go to board; SM notes systemic patterns.                                    |
| **Sprint Review**        | Stakeholders see **Done** increment; feedback becomes backlog input—not mid-sprint scope chaos.   |
| **Sprint Retrospective** | Safe enough for honesty; **fewer, better** actions with owners and dates.                         |


#### C.3 Artifacts and commitments (language check)


| Artifact            | Commitment         | Note for Filter                                                      |
| ------------------- | ------------------ | -------------------------------------------------------------------- |
| **Product Backlog** | Product Goal       | Align Epics/themes to a clear north star.                            |
| **Sprint Backlog**  | Sprint Goal        | One goal per sprint; link Jira parent/subtasks (Part 2).             |
| **Increment**       | Definition of Done | “Done” includes validation path you agreed (e.g. QA sign-off rules). |


#### C.4 When PM and SM are the same person

- **Do**: protect the team from thrash; enforce WIP and sprint goal; escalate organizational blockers; facilitate ceremonies.  
- **Avoid**: dictating **how** engineers implement; owning **all** technical assignment—delegate to tech leads; keep **Product** prioritization visibly separate where possible.  
- **Transparency**: Make backlog ordering and trade-offs visible so the team trusts priorities.

#### C.5 Anti-patterns (Scrum Master lens)

- SM as **admin clerk** only (no improvement, no impediment removal).  
- SM as **mini-project dictator** (undermines self-management).  
- Skipping **Review** or **Retro** under pressure—short-term “speed,” long-term drag.

---

### D. Using Part 5 together with Parts 2–4 (quick prompts)

- **“Apply PMP lens”** → ask for integrated sprint one-pager, risk vs issue list, stakeholder map, change impact.  
- **“Apply PRINCE2 lens”** → ask for business justification summary, stage boundary checklist, tolerances, RASCI for a decision.  
- **“Apply Scrum Master lens”** → ask for retro facilitation plan, impediment backlog, coaching angle on team agreements, inspect/adapt actions.  
- **Filter execution** → still follow **Part 2** Jira hierarchy and **Part 4** templates for Dev/QA/Automation text.  
- **Subtask sizing** → use **Part 6** and `jira-historical-data/raw/*.jsonl` (completed work in sprints Arthur→Gonzalo).

---

## Part 6 — Historical Jira data for Dev / QA / Automation estimates

### Purpose

**Effort estimates** for **Development**, **Manual QA**, and **Automation Testing** subtasks (same team composition as **Part 2**) should be **anchored in historical reality**: completed Jira work from the **reference sprints** below—not generic guesses.

When the user or agent proposes story points, hours, or days for **Dev / QA / Automation** lanes, they should:

1. **Segment** history by lane (how each issue maps to Dev vs Manual QA vs Automation is in **§6.3**).
2. **Prefer completed items** (`Done` / equivalent) from the reference sprints.
3. **Use local exports** under `**jira-historical-data/`** in this repo (see **§6.4**) so nothing is lost and estimates stay reproducible.
4. **Call out** when the new work is unlike past tickets (new tech, production escape, missing test data)—apply an **explicit buffer** or spike, not the raw median.

### Reference sprints (baseline history)

Use **all completed relevant issues** from these Jira sprints (names as used in your Jira **Sprint** field):


| #   | Sprint name        |
| --- | ------------------ |
| 1   | `sprint-Arthur`    |
| 2   | `sprint-Bertha`    |
| 3   | `sprint-Cristobal` |
| 4   | `sprint-Dolly`     |
| 5   | `sprint-Edouard`   |
| 6   | `sprint-Fay`       |
| 7   | `sprint-Gonzalo`   |


If your site uses **different spellings** (e.g. board-specific sprint IDs), store the exact **JQL** you used in `jira-historical-data/manifest.json` so exports stay repeatable.

### Estimation approach (practical)


| Step | Action                                                                                                                                                                                                                  |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Classify each historical issue into **Dev**, **Manual QA**, or **Automation** (§6.3).                                                                                                                                   |
| 2    | For each lane, compute **distribution** of actual effort: e.g. **elapsed calendar days** from first “in progress” to **Done**, **logged hours** (`timespent` / worklogs), and/or **story points** if consistently used. |
| 3    | Propose new subtask estimates using **median** or **50th–75th percentile** for “normal” work; use **p90** or explicit risk buffer for escapes, cross-stack, or unclear scope.                                           |
| 4    | Record **which historical keys** you compared (for auditability in planning notes).                                                                                                                                     |


**Team composition** for interpreting assignees and lanes: use **Part 2 roster** (developers vs Pri./Sr. QA vs SDETs).

### Mapping issues to Dev / QA / Automation lanes

Use this order:

1. **Jira issue type + naming** — e.g. subtasks labeled or typed as Development vs QA vs Automation (if your project uses distinct types or components).
2. **Summary / component** — keywords (`QA`, `Test`, `Automation`, `SDET`, `regression`, `E2E`).
3. **Assignee role** — match assignee to **Part 2** tables (developers → Dev lane; Altamash / Surabhi / Ayesha → Manual QA; Amit / Rachit → Automation).
4. **Parent story** — if only one subtask exists, inherit lane from the **dominant** work (e.g. coding vs validation).

If mapping is ambiguous, **exclude** that issue from automatic baselines or tag it **low confidence** in your summary stats.

### Local storage: lossless / large datasets

All raw historical data should live under:

```text
FilterSprintPlanning/jira-historical-data/
  manifest.json              # sprint list, export date, JQL, field list
  EXPORT-INSTRUCTIONS.txt    # how to re-export without truncation
  raw/
    sprint-Arthur.jsonl      # one JSON object per line (recommended)
    sprint-Bertha.jsonl
    sprint-Cristobal.jsonl
    sprint-Dolly.jsonl
    sprint-Edouard.jsonl
    sprint-Fay.jsonl
    sprint-Gonzalo.jsonl
    optional: full-export-YYYYMMDD.zip   # exact copy of Jira CSV/API dump
```

**Why JSON Lines (`.jsonl`)?** Each issue is one line—safe for **very large** exports, easy to append, and **no row truncation** from spreadsheet limits.

**Lossless export checklist (Jira Cloud / Data Center):**

- Include **all fields** you rely on: at minimum `key`, `issuetype`, `parent`, `summary`, `status`, `resolution`, `resolutiondate`, `created`, `updated`, `assignee`, `reporter`, `priority`, `labels`, `components`, `fixVersions`, **Sprint**, **time tracking** (`timeoriginalestimate`, `timeestimate`, `timespent`, `aggregatetimespent`, `workratio`), **story points** (custom field id varies by site), `description` (export **ADF JSON** if you need full fidelity), `subtasks`, `issuelinks`, `comment` (optional—very large).  
- Prefer **Jira issue navigator → Export** or **REST `/rest/api/3/search` with `expand=changelog,renderedFields`** when you need **full history** (slower, larger).  
- **Do not** rely on Excel alone for huge exports (row limits); use **CSV full download** or **API pagination** until `total` issues are retrieved.  
- Store **one file per sprint** plus a **dated full backup** (`full-export-YYYYMMDD.zip`) when you run a complete refresh.

After each import, update `**manifest.json`**: `last_export_utc`, `issue_counts` per file, and the **exact JQL** used.

### Agent / human prompt snippet

> “Estimate Dev, QA, and Automation subtasks using historical completed issues from sprints sprint-Arthur through sprint-Gonzalo; read `jira-historical-data/raw/*.jsonl` and Part 2 roster; show medians and comparable issue keys.”

---

*End of consolidated document.*