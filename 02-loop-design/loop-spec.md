# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering, ★ Deliverable 2
>
> ✅ **What this validates:** the agent knows when to run and when to stop, by the end you'll have proven a one-page Loop Spec with a trigger, a definition of "done," and explicit stop conditions.
>
> Your one-page blueprint for how the work you handed to the agent (M1) actually *runs*.
> An agent is just a prompt that fires itself, this spec says when it fires, what "done" means, and what it needs to do the job. Living document; refine as the course progresses.

## 1. Trigger & loop type

**Chosen type:** Cron, primary only.

**Why:** I want to start every week by reading one full recap of the previous week, so a fixed Monday 8am Pacific run is the right fit.

**Status:** The schedule is planned. Today I run it by hand with `python3 agent.py`.

**Ruled out:**
- **Hook:** it would draft every time something happens, but I want one weekly recap, not many partial ones.
- **Heartbeat:** constant checking is noisy and costly for something I read once a week.
- **Goal:** there's no open-ended target to chase; the job is a fixed weekly report.

**Dedupe (planned, alongside the schedule):** One draft per week. Cortex labels each draft with the week it covers. If a draft for that week already exists, it skips and logs "already drafted" instead of creating a second one.
- A real recap draft counts as the week's draft. That includes a hand-off draft waiting for my decision, so a rerun doesn't create a second one while I'm reviewing it.
- A failure note does not count, so a rerun after a failure can try again.

## 2. Goal / definition of done

**Done means:** one weekly recap draft, saved for my review, with all six parts present and the critic's pass.

**The six parts:**
1. A proposed overall status (Green, Amber or Red) with a short reason, which I confirm at review.
2. What got done: key merges, shipped work and metric changes.
3. Risks and issues flagged, with any escalations called out.
4. The sources used and the ones excluded, so I can spot gaps.
5. The risks considered but not flagged.
6. Proposed stories waiting in the approval queue, if any.

**Independent check:** The critic is my independent check, so Cortex never grades its own work. If the critic contradicts itself, that is a stuck condition to catch, not a reason to loosen "done". The contradictory critic rule gets fixed in Step 4.

**Where it goes:**
- **Today:** saved as a file in `00-build/run-output/`.
- **Planned:** a draft in my email inbox, through a connection that can create drafts but cannot send.
- Nothing goes to anyone else in either case.

## 3. Stop conditions

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | All six parts are present and the critic has passed the draft. | The draft is saved for my review. Nothing goes to anyone else. |
| **Stuck / give up** | Any of these:<br>• Last week's data can't be pulled after 3 tries (temporary failures only).<br>• The project isn't found. This is a hard stop with no retries, and Cortex never substitutes another project.<br>• The critic's rejections ask for opposite changes, or the same reason comes back after a revision.<br>• 2 revisions are used up, or the $0.50 cost cap is hit. | Cortex stops and sends me a short failure note saying it couldn't finish and why. A failure note does not count as the week's draft, so a rerun can try again. |
| **Escalate to human** | Any of these:<br>• The draft or the request would commit to a date.<br>• Any open Sev-1 or launch hold.<br>• More than 10 proposed stories.<br>• The notes contain instructions to post or share something. | Cortex holds the draft with each blocked item clearly marked, such as "needs your decision: GA date". It leaves out the part it can't decide instead of guessing. A draft with a blocked part must never look complete when I skim it. Lower risks still appear in part 5 of every draft. |

**Status is proposed, not final.** Every draft waits for my review and nothing is sent, so I own the status decision at review time. Cortex labels the status "proposed" and I confirm it.

## 4. State

**State is locked.** Scope is per project, with no cross-project leakage.

**Persists across runs:**
- **Read-only references:** past updates, decision log, roadmap, team norms.
- **Saved with each draft:** the sources used and excluded, and the risks considered but not flagged. These are a record for me only, never fed back to Cortex.
- **A small run log (planned unless built in Step 4):** one log per project, one line per run, with the week covered, the outcome (draft, hand-off, failure note or skipped "already drafted") and the stop reason. The dedupe key is project plus week. Run facts only, never draft content or claims. Cortex reads it only to check for duplicates, never as source material for a draft.

**Why a log:** my dedupe and failure notes both need a record of what each run did, and scanning drafts for a week label can fail silently.

**Not remembered:** rejected or unapproved drafts, so a claim already judged wrong can't come back as reference. Anything from `.env`. Personal details from activity data beyond what the current update needs.

**Purged after each run:** everything else, including the critic's reasons and the revision count.

## 5. The five things a loop can lean on

_`state` is always-on. `connectors` only if you already have one wired (e.g. a Jira key or Google MCP), otherwise just note it as a plan. `skills`, `subagents`, `work tree` scale with autonomy; "not needed yet, because…" is a valid answer._

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run, a git worktree) | Not needed yet: runs are read-only and write only a draft file, so there's no code to isolate. Add one per run when Cortex starts writing anything beyond a draft. |
| **Skills** (reusable capabilities) | Not needed yet: the format and rules sit in the prompt and the team norms. Package the recap format as a skill once a second report type exists. |
| **Plugins / connectors** (tools & access, optional if you don't have one yet) | No connector is wired today. Cortex reads fixture files only. Planned:<br>• The scheduler that fires the Monday 8am Pacific run.<br>• A draft-only email connection that can create drafts but cannot send.<br>• Later, live project data from Jira or GitHub instead of the sample files. |
| **Subagents** (independent check when the loop can't grade itself) | The critic already acts as my independent check. The full design is left for M3's `orchestration-map.md`. |
| **State tracking** | Locked in §4: per project, with a small run log (planned). |

> Context plan (M4) and the hand-off to bounds & evals (M5) come in later modules, you'll add them to their own deliverables then, not here.

## Link to live loop

_[path to your agent in `00-build/`]_
