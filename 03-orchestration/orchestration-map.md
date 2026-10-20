# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> ✅ **What this validates:** nothing advances unchecked, by the end you'll have proven a justified topology, a roster, and a validator with a defined fail action.
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

**Design today:** A single Monday-8am cron-triggered agent that pulls one project's data, drafts a six-part weekly recap with a proposed status, and saves it for my review. A separate critic call checks the draft first, with a cap of 2 revisions and a $0.50 cost limit.

**Decision: split for the independent validator only.**

| Reason | Applies? | Why / why not |
|---|---|---|
| Separation of concerns | No, but watch it | Cortex does two jobs, a recap from activity and story proposals from the PRD. They're kept apart today by the six-part format and the critic checking claims against activity. If story ideas start leaking into the recap as if they happened, that's my trigger to split. |
| Parallelism | No | It's a weekly run I read once, and five quick reads don't need to be faster. |
| Independent validator | **Yes** | Cortex never grades its own work, so a separate critic on a stronger model checks the draft against the source data. |
| Context-window pressure | No | The data is small and a run costs under a cent. |

## 2. Topology

**Pattern:** single + subagent (one drafting agent, one critic)

```
[Monday 8am cron, today: python3 agent.py]
        ↓
[Cortex: pulls one project's data, drafts six-part recap + queues stories]
        ↓
[Code checks, no model call: six parts present? date asked for but unmarked?]
   fail ↘                            pass ↓
        ↓                       [Critic: 5 checks, fixed labels]
        ↓                    fail ↙           pass ↓
   back to Cortex with labelled reasons    [Hand-off needed? (blocked item / escalation)]
   (max 2 revisions)                          yes ↙        no ↘
   stuck or cap hit → failure note     [Hand-off draft]  [Draft]
   (not a draft; rejected draft saved separately)     ↓
                                          [PM review checkpoint: saved to run-output/, nothing sent]
```

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| Cortex (`gpt-4o-mini`) | Pulls project data, drafts the six-part recap, proposes stories | M2 loop (cron, one draft per week) |
| Critic (`gpt-4o`) | Checks the draft against the source data on five checks and returns labelled pass/fail | Runs inside the same loop as Cortex's independent check; it has no loop of its own |
| Code checks (not an agent) | Six-part completeness and unmarked-date check, run before the critic | Part of the M2 loop's "done" definition |

## 4. Communication & hand-offs

- **Cortex → code checks → critic:** the proposed draft text plus the source log of what Cortex pulled, in the same process, and the code adds the team norms. The critic call gets only those three things: the source log, the team norms and the draft.
- **Critic → Cortex (on fail):** one message with each reason as `LABEL: detail`, then "Fix it."
- **Out to me:** a file in `run-output/` (draft, hand-off draft, or failure note plus a labelled rejected draft).
- **Hand-off drafts** (with "NEEDS YOUR DECISION:" lines) go through the critic like any other draft and get the full review.
- **Protocol:** plain in-process hand-offs. No MCP or A2A, since there's one critic and it's a function call.

## 5. The validator

**Critic:** a separate model call (`critic.py`, `gpt-4o`) that never sees Cortex's drafting context. It gets only the source data, the team norms (always supplied by the code as a separate section, whatever Cortex looked up) and the proposed output. It returns pass/fail, the rubric's status and the proposed status, and reasons, each with one fixed label and the item it is about.

**What it checks (five checks, mapped to labels):**

| # | Check | Fail labels |
|---|---|---|
| 1 | **Grounded claims.** No number, merge or date in the recap that isn't in the pulled data, and the update is about the right project. | `WRONG_PROJECT`, `UNSUPPORTED_CONTENT` |
| 2 | **Sources used and excluded.** The excluded list names real data Cortex pulled and left out, with a reason. "Excluded: None" fails. | `MISSING_CONTENT`, `UNSUPPORTED_CONTENT` |
| 3 | **Status matches the rubric.** The proposed Green, Amber or Red follows the written rubric and nothing else. | `STATUS_TOO_HIGH`, `STATUS_TOO_LOW` |
| 4 | **Norms and authority.** No unconfirmed date or launch commitment, no confidential item, nothing posted or committed, and any instruction to post or share is refused and escalated. | `NORMS_VIOLATION`, `POSTED_OR_COMMITTED`, `JAILBREAK_NOT_HANDLED` |
| 5 | **All six parts present.** Every section is there, and any blocked item is marked "NEEDS YOUR DECISION" rather than guessed. | `MISSING_PART` (and `UNSUPPORTED_CONTENT` if a blocked item was guessed) |

**Known misses (M5 eval cases, confirmed on real runs, not fixed):** the critic passed "Excluded: None"; it passed a draft that named a confidential item (Orbit) in the Excluded list; it demanded data the source lacks, which led Cortex to invent "Current NPS is 72" (a later critic caught it); and a hand-off silently dropped a requested item (weekly active users) with no marker. It also passed Amber where the rubric said Green earlier, and caught it in the M3 runs, so that case stays as an eval case too.

**Fail-action (three tiers):**
1. **Revise:** the draft goes back to Cortex with the labelled reasons, up to **2 revisions**. One revision fixes a clear problem, and a second covers anything the first fix uncovers.
2. **Give up:** if the critic's rejections ask for opposite changes about the same item, or the same reason comes back after a revision, or the cap is used up, Cortex stops and saves a short failure note. The failure note does not count as the week's draft, so a rerun can try again.
3. **Hand off:** an escalation trigger produces a hand-off draft with each blocked item marked.

**Revision cap: 2, then give up.** After that, retrying rarely helps, and the stuck check already stops repeats earlier. If it hits the cap, I read the failure note and the rejected draft (saved in its own labelled file), then decide whether the data, the prompt or the rubric needs fixing, or write that week's update myself. The cap is also a Module 5 bound, so it stays as it is.

**Pass-action:** a passing draft is saved to `run-output/` for my review and nothing is sent. Planned: the same draft goes to my email inbox through a draft-only connection.

**Stuck check, built (item 16):** opposite labels (such as `UNSUPPORTED_CONTENT` and `MISSING_CONTENT`) count as opposite only when they point at the same item. Seen on a real run: `claim: nps` and then `claim: current nps is 72` were different items, so the run was correctly not called stuck.

**Status direction, in code (items 20 and 21):** the critic names the rubric's status and the proposed status, and the code sets `STATUS_TOO_HIGH` or `STATUS_TOO_LOW` from the order Red < Amber < Green. The critic mislabelled the direction in real runs, and a prompt rule did not fix it. If the two statuses differ, the code adds the status reason and fails the verdict even if the critic said pass. It only enforces the critic's own fields. The label correction is seen on a real run; the pass-to-fail enforcement is built but not yet shown in a run.

**Prompt-level fixes that did not hold (items 18 and 19):** telling the critic never to demand data the source lacks, and telling Cortex never to name confidential items, both failed on a real run. They stay as prompt rules, with M5 eval cases, and are not enforced in code.

**Before the critic (code, no model call):** a six-part completeness check (`MISSING_PART`) and an unmarked-date check (`NORMS_VIOLATION`) run first.

**Reduced review:** only a no-recap `ESCALATE:` output is judged on posting, commitments and leaks alone. A hand-off draft with "NEEDS YOUR DECISION:" lines gets the full review.

## 6. State: shared vs isolated

**Shared:** the source data Cortex pulled (the source log), the draft, and the team norms (always supplied by the code, whatever Cortex looked up). That's what the critic needs to check claims and the rubric.

**Isolated:** Cortex's reasoning and tool-call history stay hidden from the critic, so it can't be talked into agreeing. The critic gets no past updates. Tone and precedent are my call at review, not the critic's. Each critic call is fresh, and its reasons reach Cortex only as labels plus a short detail, then are purged after the run.

**Never read:** the run log, `.env`, or `run-output/` as source material.

## 7. Cost & latency budget

**What the critic costs (observed on real runs; `gpt-4o` critic, `gpt-4o-mini` drafter):**
- A clean pass adds one critic call. About 1 cent was measured on the M2 happy path ($0.0075, with the older, smaller critic prompt). A run with one rejection and a pass cost about 2 cents ($0.022 to $0.023, 14 to 15 seconds).
- Each extra critic round (a rejection plus a revision) adds about 1 to 1.5 cents and about 8 seconds.
- The worst observed run was about $0.04 and 23 seconds, at the revision cap (3 critic calls and 2 extra Cortex passes). Weekly, that is up to about $2 a year per project.
- The critic is probably the main cost, because it runs on `gpt-4o` (about 17 times the price per token of `gpt-4o-mini`). That is the price of an independent check. The run total is not split by model, so this is not measured.
- The code checks (six parts, unmarked date) cost nothing: no model call.

**Bounds:** the enforced bounds stay as they are: 2 revisions and the $0.50 cost cap. $0.50 is about 13 times the worst observed run, so it is a runaway backstop, not a budget. I'll decide whether to tighten it in M5 (`05-bounds-evals/bounds-and-evals.md`). **No latency bound:** it runs Monday at 8am and I read it later, so a few seconds either way doesn't matter.
