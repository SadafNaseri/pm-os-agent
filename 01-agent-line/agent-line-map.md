# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| # | Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Above / Below | HITL? |
|---|---|---|---|---|---|---|
| 1 | Pull project state + activity | H | L | H | Below | No |
| 2 | Decide relevant context | H | M | L (raw) → M with checkpoint | Below | Yes: Cortex lists the sources it used and excluded so a human can spot gaps |
| 3 | Draft the update | H | L | H | Below | No |
| 4 | Decide tone/commitment level | L | H | L | Above | No |
| 5 | Flag at-risk / escalation | H | L | M | Below | Yes: Cortex shows the risks it considered but chose not to flag so a human can catch a missed one |
| 6 | Choose what to escalate | M | H | L | Above | No |
| 7 | Propose a story batch (capped) | H | M | M | Below | Yes: approval queue |
| 8a | Post a routine update | L | M | M | Above | No |
| 8b | Approve a company-wide update | L | H | M | Above | No |

## Agent anatomy (sketch)

- **Model:** `gpt-4o-mini` is the default for the mechanical steps (1, 3, 7). A stronger model handles items 2 and 5, where missed sources and missed flags are invisible, and the critic, because a critic as weak as the drafter can't catch its mistakes. If the critic rejects a draft, retry once on the stronger model before escalating to a human; the per-run cost cap keeps that bounded.
- **Tools:**
  - **Present (read):** `get_project`, `get_activity`, `search_past_updates`, `get_roadmap`, `get_norms`.
  - **Present (write, queue only):** `propose_stories`, capped.
  - **Deliberately absent:**
    - post or send to any channel (8a, 8b)
    - create, merge or close PRs and tickets
    - write directly to the backlog, bypassing the approval queue (7)
    - change a status, launch gate or date (4)
  - **How the line is enforced:** posting, creating, merging and changing status, gates or dates are enforced by Cortex having no tool for them. Tone/commitment (4) and what to escalate (6) have no tool to remove, so they rely on the critic and human review.
  - **M2 design gap:** the item 2 and item 5 checkpoints (sources used/excluded, risks considered but not flagged) are outputs Cortex must produce, not tools.
- **Memory:**
  - **Persists (read-only reference):** past updates, decision log, roadmap, team norms.
  - **Kept with the saved draft:** the item 2 sources used/excluded list and the item 5 risks considered but not flagged list, as a record of what Cortex relied on and what it chose not to raise. Kept for the human, never fed back to Cortex.
  - **Explicitly not remembered:**
    - rejected or unapproved drafts, so a claim already judged wrong can't come back as reference in a later run
    - anything from `.env`
    - personal details from activity data beyond what the current update needs
  - **Everything else is purged after each run.**
- **Loop:** _placeholder, defined in M2 loop-spec.md_
- **Bounds:** _placeholder, defined in M5 bounds-and-evals.md_
- **Evals:** _placeholder, defined in M5 bounds-and-evals.md_

## The golden rule, applied

**Below the line**

- **#1 Pull project state + activity:** It only reads data, so a bad pull changes nothing and is easy to check against the source.
- **#2 Decide relevant context (HITL):** A missed source is invisible in the draft, so Cortex lists what it used and excluded before I trust the update.
- **#3 Draft the update:** A draft is only words in a file, checked against the data before anything is sent.
- **#5 Flag at-risk / escalation (HITL):** A false alarm costs me a minute but a missed flag hides a risk, so I review what Cortex chose not to flag.
- **#7 Propose a story batch (HITL):** Bad stories could shape a sprint, so the cap limits how many and nothing enters the backlog without my approval.

**Above the line**

- **#4 Decide tone/commitment level:** A "green" status or a ship date is a promise in my name, and once someone reads it I can't take it back.
- **#6 Choose what to escalate:** If Cortex decides a risk isn't worth raising, I never see it, and I can't measure a failure I can't see.
- **#8a Post a routine update:** A posted update can't be unsent, even to a small audience.
- **#8b Approve a company-wide update:** It can't be unsent, and it reaches everyone, including people who will act on it.

## Hardest call

Deciding what context to include (item 2) was my hardest call. A reviewer can see what's in the draft but not what was left out, so a missed source is invisible, and its raw measurability is Low. By the golden rule that should put it above the line. Listing the sources used and excluded is what makes it safe below the line, because it lets me spot gaps.
