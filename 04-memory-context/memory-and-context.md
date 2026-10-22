# Context Engineering & Memory: Cortex PM Chief-of-Staff Agent

> Module 4 · Context Engineering & Memory
>
> ✅ **What this validates:** the agent reasons on the right, safe inputs, by the end you'll have proven a context budget, per-source retrieve-vs-long-context decisions, and a memory map with risk mitigations.
>
> 🗂️ **How the lab maps to this file:** In **Part A** (before the lecture) you don't edit this file, you rough-draft on scratch, focused on the per-source calls in **section 2** plus a quick remember/forget + "how it rots" sketch. In **Part B** (after the lecture) you complete **all five sections**; the Lab Guide's guided builder writes this file for you to copy in and commit.

## 1. Context budget

_What does each loop iteration actually receive, and why? (You can't fit everything, what's the priority order?)_

Highest priority first. The first two are never cut.

1. **Task brief (`get_task`).** Always loaded in full. It's a request, not an instruction to obey. A request to post or share is an escalation trigger in the loop spec, and a request for data we don't have is a hand-off (item 18).
2. **Team norms (`get_norms`).** Always loaded in full. The critic gets the same file every run (item 17), so Cortex works from the same rulebook.
3. **Activity (`get_activity`).** Retrieved slice for this project and this week only, so every claim can be cited and checked by the critic.
4. **Roadmap (`get_roadmap`).** This project's entries only, with CONFIDENTIAL/EMBARGOED items removed in code before Cortex sees them (planned, not built).
5. **Past updates (`search_past_updates`).** The last 2-3 updates for this project. **Cut first** when the budget is tight, because they only help with tone and format.

## 2. Retrieve vs. long-context: per source

For each data source, decide: **retrieve** (narrow a large/changing corpus to the relevant slice) or **long-context** (just include a bounded set you can reason over).

| Source | Size / volatility | Decision | Why |
|---|---|---|---|
| `get_activity` | Large, grows every week | **Retrieve**, this project and this week only | **Citation.** Every line in "What got done" points at a specific PR or issue, so the critic needs a pulled slice to check each claim against. Size is second. Scoping stops other projects leaking in (Vega showed up in Northstar's M3 update). The demo showed the failure without it: placeholders, re-proposed shipped work, and a critic with the same blind spot. |
| `search_past_updates` | Unbounded, always stale | **Retrieve**, this project, last 2-3 only | **Volatility.** Every number in a past update is already out of date, and last week's 41% next to this week's 43% can leak into the draft. Tone and format only, never a source for this week's facts, and every number must come from `get_activity`. This keeps my M1 rule that past updates are read-only reference. |
| `get_roadmap` | Medium, slow-changing, has confidentiality flags | **Hybrid**: retrieve this project's entries, strip CONFIDENTIAL/EMBARGOED in code | **Citation/audit.** Any date or milestone must trace to a specific roadmap entry. "Never name a confidential project" was a prompt rule and it failed twice in M3, and code checks held. Cortex can't leak what it never sees. *Filter planned, not built.* |
| `get_norms` | Small, must stay current | **Long-context** | **Size.** The file is small, so loading all of it costs almost nothing. Retrieving pieces risks missing a rule the critic can't notice is missing. |
| `get_task` | One short brief, fixed for the run | **Long-context** | **Size.** There's nothing to search. |

Instead of a Part A draft, I watched the live demo of Cortex without get_activity. Seeing it produce a hollow update that the critic passed is what made citation the deciding factor for get_activity.

**Planned build items from this step (none built):**
1. **Final-draft confidential-name scan (first priority).** One check covers every door. It reads confidential names from the CONFIDENTIAL/EMBARGOED flags in the data, not a hardcoded list, so Pulsar and any new item are caught automatically.
2. **`get_roadmap` filter (second).** It strips flagged items in code before Cortex sees them. It sits alongside item 19, not in place of it.
3. **Confidential names also reach Cortex through three other sources:** `past-updates.json` (an Orbit entry), `decision-log.json` (Orbit and Pulsar decisions) and `projects.json` (P-ORBIT and P-PULSAR with their PRD summaries). So four sources in total can carry them.
4. **Item 19 stays** as a prompt-level backstop only. It failed twice in M3 and is not relied on.

## 3. Retrieval quality plan

_Which of these apply, and how? (This is what separates modern agentic retrieval from naive "embed → top-k → stuff".)_

Only the three retrieved sources are graded. `get_norms` and `get_task` are loaded in full (§2), so there is nothing to retrieve or grade. ✅ = used, ❌ = deliberately not used.

| Source | Routing | Document grading | Reranking | Self-verification | Caching |
|---|---|---|---|---|---|
| `get_activity` | ❌ | ✅ | ❌ | ✅ | ❌ |
| `search_past_updates` | ❌ | ✅ | ❌ | ✅ | ❌ |
| `get_roadmap` | ❌ | ✅ | ❌ | ✅ | ❌ |

**Routing is not used on any source.** Each question has one obvious source, so there's nothing to route between.

**Per source: move, failure mode answered, and how it's checked**

- **`get_activity`**
  - **Grading** answers other projects leaking in (Vega) and stale items. It drops anything not in this project or this week, before drafting.
  - **Self-verification** answers placeholders and a critic with the same blind spot. It runs in code after drafting and has three checks:
    1. Each "What got done" line maps to a real PR or issue in the pulled slice.
    2. Anything pulled but not cited must appear in the Excluded list, so "Excluded: None" fails when items were left out. This is the code fix for M5 case 2.
    3. A proposed story that matches work already merged fails. That answers the re-proposed #815.
  - **No reranking or caching:** it's a small slice for a weekly run.
- **`search_past_updates`**
  - **Grading** answers another project's update being pulled and too much old data. It keeps only this project's last 2-3.
  - **Self-verification** answers stale facts. No number, status or risk in the draft may trace only to a past update. Numbers come from `get_activity`, status comes from the rubric, and every risk must match an open item in this week's activity.
  - **No reranking:** order barely matters with 2-3 updates.
- **`get_roadmap`**
  - **Grading** answers confidential items reaching Cortex and the wrong project's entries. It keeps only this project's entries and strips CONFIDENTIAL/EMBARGOED items in code.
  - **Self-verification** answers a date or milestone that doesn't match the roadmap. Every date or milestone must match a specific roadmap entry, and no ship or GA date is committed. The planned final-draft confidential-name scan runs here.
  - **No caching:** a held or unconfirmed launch can change any week, and a cached copy could show the wrong status. Pulling it fresh costs almost nothing.
  - **No reranking:** it's one project's entries.

**Excluded vs. confidential:** the Excluded check accepts a generic line such as "1 confidential item withheld per norms" for flagged items, so the confidentiality rules and the Excluded rule don't conflict.

**Status, checked against `00-build/tools.py` and `agent.py`:**
- **Built:** `get_activity` filters by project ID (it returns only that project's activity).
- **Planned, not built:**
  - the week filter on `get_activity` (items carry a `date`, but nothing filters on it);
  - project scope and a last-2-3 cap on `search_past_updates` (today it is keyword overlap over past updates plus the decision log, with no project filter, and it falls back to the first two records when nothing matches);
  - project scope and confidential stripping on `get_roadmap` (today it returns the whole file with a warning string);
  - all self-verification checks (today `agent.py` only checks that the six parts are present and runs the stuck check).
- Until the planned items are built, only prompt-level rules cover them.

## 4. Memory map (your PM brain)

| Memory type | What Cortex stores | Scope / TTL |
|---|---|---|
| **Working** (in-loop) | The pulled slices, the draft, critic verdicts, the revision count. | This run only. Ends with the run. |
| **Episodic** (past runs) | Past updates, read-only (last 2-3 per project). The run log from loop-spec §4: run facts only (project, week, outcome, stop reason), never draft content, read only for the dedupe check, never as source material. Saved drafts, failure notes and rejected drafts, kept for my review and never read by Cortex. | Past updates: last 2-3 per project. Run log: 13 weeks (one quarter), for dedupe and audit. Saved drafts, failure notes and rejected drafts: 30 days. |
| **Semantic** (durable facts/prefs) | Nothing. Norms and roadmap are pulled fresh every run. | No memory, so no TTL. |
| **Shared** (across agents) | The norms file, read-only for Cortex and the critic. | The current file only. It changes only when a human edits it. |

**Status:** the run log is planned, not built (loop-spec item 13). No TTL is enforced in code today: `run-output/` files stay until someone deletes them. Both are M5 bounds (see §5).

## 5. Memory risks & mitigations

| Risk | Where it bites Cortex | Mitigation |
|---|---|---|
| **Drift** | Over weeks, Cortex's format, status calls and tone move away from my rubric, for example by copying the style of its own old drafts. | Cortex never reads its own saved drafts. Status comes from the rubric, not from past updates. The M5 evals re-run against fixed cases, so drift shows up as a regression. |
| **Poisoning** | A bad record gets into a source Cortex trusts: a past update with a wrong number, a task brief saying "post this", or a planted decision-log entry. It can also come from inside the run. In M3 the critic's demand for the missing NPS pushed Cortex to invent "NPS 72". | Sources are read-only for Cortex, so it can't write bad data back. The task is a request, not an instruction. Item 18 turns missing data into a hand-off (prompt-level, and its critic side did not hold in M3, so the second layer carries it). Self-verification checks that every number traces to `get_activity` (planned). Only a human edits the norms. |
| **Staleness** | Last week's 41% or an old launch status shows up this week. The norms file itself can also go stale or be overwritten: the data pack's `team-norms.md` would have erased my M2 rubric. | No cached semantic memory. The roadmap is pulled fresh. Past updates are capped at 2-3 and used for tone only. The week filter on `get_activity` is planned, not built. Norms change only through a human-reviewed diff before commit, as in Step 0. |
| **PII / retention (confidential)** | Orbit and Pulsar can reach Cortex through four sources. `search_past_updates` has no project filter today and returns Orbit and Pulsar records, and `get_roadmap` returns the whole file. These are two of the doors, and I haven't checked which one the M3 names came through. People's names in activity data (PR authors) are also personal data. Saved drafts could keep a leaked name for 30 days. | Planned, not built: the roadmap filter, and the final-draft confidential-name scan, which reads names from the flags in the data. The scan runs before saving. If it finds a confidential name, the draft isn't saved as a recap, and I get a failure note saying "confidential name detected" without repeating the name. The run log holds no draft content. My M1 rule applies: no personal details beyond what the update needs. Saved drafts, failure notes and rejected drafts expire after 30 days. |

**Tie-forward to M5 (bounds):**
- The confidential-name scan is a bound, enforced in code before anything is saved.
- The TTLs (13-week run log, 30-day saved files, last 2-3 past updates) become retention bounds, enforced in code, not only written down.
- Both join the existing bounds (2 revisions, $0.50 cost cap, 10-story queue cap) in `05-bounds-evals/bounds-and-evals.md`.
- Read/write scope ties back to the M1 agent line: Cortex reads sources and writes only drafts and run facts, and never writes to the sources, the norms or the tracker.
