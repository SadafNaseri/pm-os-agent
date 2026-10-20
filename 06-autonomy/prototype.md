# Prototype: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 1, the working agent demo
>
> ✅ **What this validates:** the agent actually runs end to end, by the end you'll have proven it with real screenshots of your Cortex across the six required moments (M2 to M6).

## What it does

_One paragraph: the agent in action, end to end._

## How you built it

- **Coding agent:** _which one you directed (Claude Code / Cursor / Codex)_
- **Model + bounds:** _model used, max iterations, cost cap, queue cap_
- **Repo / config:** _path to your build in `00-build/`_
- **Live link:** _[shareable URL, optional bonus]_

## Screenshots (required, collected M2 to M6)

Real screenshots of *your* Cortex running. These are the `00-build/CORTEX-ANATOMY.md` set and they are required, a link alone is not enough.

| # | Screenshot | What it shows | From |
|---|---|---|---|
| 1 | ![Critic pass and HITL checkpoint](screenshots/m2-run1-happy-critic-pass-checkpoint.png) | happy-path run: a real drafted update + the HITL checkpoint (queued, not posted) | M2 |
| 2 | ![Critic rejects tampered draft](screenshots/m3-critic-rejects-tampered-draft.png) | the critic rejecting a bad draft (revise/block)<br>*Injected fault: the draft was edited before the critic (41% → 47%, plus an invented WAU/NPS line). The real critic rejected it with UNSUPPORTED_CONTENT; Cortex revised; the critic passed. This capture predates the item 20 fix, so the status reason still shows the old STATUS_TOO_HIGH mislabel.* | M3 |
| 3 | _[img]_ | a grounded update citing pulled activity + a caught hallucination | M4 |
| 4 | _[img]_ | jailbreak refused + escalated | M5 |
| 5 | _[img]_ | an iteration/cost/queue bound halting a runaway | M5 |
| 6 | _[img]_ | end-to-end run | M6 |

## M2 loop runs (stop conditions firing)

Real runs of Cortex against the M2 loop spec (`02-loop-design/loop-spec.md`), grouped by what they show.

### Live stuck check, opposite reasons (earlier run, before the stronger critic)

![Earlier draft in the rerun](screenshots/m2-run1-draft-output.png)
*Earlier draft in the rerun: all six parts present, before the "Used" list was limited to read tools.*

![Stuck check fires on opposite critic reasons](screenshots/m2-run1-stuck-check-fired.png)
*Stuck check fires: the critic's reasons flipped from STATUS_TOO_HIGH to STATUS_TOO_LOW, so Cortex gave up with a failure note before the revision cap.*

### Happy path success, HITL checkpoint

![Happy-path draft](screenshots/m2-run1-happy-draft.png)
*Happy path: Cortex pulls five sources, queues 3 stories, and drafts the six-part update with a proposed Amber status.*

![Critic pass and HITL checkpoint](screenshots/m2-run1-happy-critic-pass-checkpoint.png)
*Critic passes, draft saved, nothing posted, run cost ≈ $0.0075. This run shows Amber and "Excluded: None", the two critic misses logged as M5 eval cases.*

### Missing data, hard stop and give-up

![Missing project, hard stop](screenshots/m2-run2-missing-data-giveup.png)
*Missing project: `project_not_found` stops the run at once (≈ $0.0002), and the failure note says to check the project ID.*

### Forced test, same reason repeats

![Forced test, Cortex draft](screenshots/m2-forced-stuck-repeat-draft.png)
*Forced test, `repeat` case: the real Cortex draft before the scripted critic rejects it.*

![Forced test, stuck check fires](screenshots/m2-forced-stuck-repeat-fired.png)
*Forced test: the same reason (UNSUPPORTED_CONTENT) returns after a revision, so Cortex gives up as stuck.*

## M3 evidence (the critic, orchestration and its misses)

Real runs against the M3 critic (`03-orchestration/orchestration-map.md`). Row 2 of the table above is the required rejection capture. Misses are logged as M5 eval cases in `02-loop-design/step4-build-changes.md`.

### Forced test, tampered draft (injected fault)

![Tamper test, Cortex draft](screenshots/m3-tamper-draft.png)
*Real Cortex draft on the happy path, before the fault is injected (proposed Amber, activation rate 41%).*

![Tamper test, revision passes](screenshots/m3-tamper-revision-pass.png)
*After the rejection shown in row 2, Cortex's revision (Green, generic confidential entry) passes the critic and is saved. Run cost ≈ $0.0223.*

### Missing data, first run (before items 18 to 20)

![First invented-metric draft](screenshots/m3-invented-metric-draft.png)
*`invented-metric`: Cortex does not invent the numbers. It says NPS is "not available" and names Orbit in the Excluded list.*

![Critic rejects, demands the metrics](screenshots/m3-invented-metric-critic-reject.png)
*The critic rejects Amber (STATUS_TOO_LOW) and demands the missing weekly active users and NPS (MISSING_CONTENT); Cortex's revision then writes "X% (exact number needed)".*

![Give-up as stuck](screenshots/m3-invented-metric-giveup.png)
*The critic repeats MISSING_CONTENT, so Cortex gives up as stuck with a short failure note. Run cost ≈ $0.0235.*

### Missing data, after the fixes

![Hand-off after items 18 and 19](screenshots/m3-invented-metric-handoff.png)
*The critic asks for a NEEDS YOUR DECISION marker instead of a number, Cortex revises, and the run ends as a hand-off (≈ $0.0232). It also shows Amber labelled STATUS_TOO_HIGH and "Excluded: None" passing, both logged as M5 cases.*

![Code corrects the status label](screenshots/m3-item20-label-corrected.png)
*Item 20 in code: the critic labelled Amber as STATUS_TOO_HIGH and the code corrected it to STATUS_TOO_LOW (rubric Green, proposed Amber).*

![Critic catches a fabricated NPS](screenshots/m3-critic-catches-fabricated-nps.png)
*Critic caught a real fabrication (NPS 72) that an earlier critic demand caused.*

![Final hand-off, with misses](screenshots/m3-invented-metric-handoff-final.png)
*Final hand-off (≈ $0.0381): only NPS is flagged (weekly active users silently dropped), and the Excluded list names Vega and Orbit. Evidence for M5 cases 3 and 5.*

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._
