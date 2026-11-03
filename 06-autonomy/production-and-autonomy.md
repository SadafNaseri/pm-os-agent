# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 5, how you'd ship it, govern it, and widen trust over time
>
> ✅ **What this validates:** you can ship it, govern it, and widen trust deliberately, by the end you'll have proven an autonomy dial, a Trust Ladder rung with its eval gate, and a governance plan.

## Autonomy Dial by segment

Autonomy is a product decision per user, not one global setting. The dial sets how many below-the-line checkpoints still pause for a user (the story approval queue, the sources used/excluded list, the risks considered but not flagged). It never moves the M1 agent line: posting or sending any update stays above the line for every segment, and Cortex has no send tool.

| Segment | Desired autonomy | Why |
|---|---|---|
| **Me** (weekly leadership recap) | **Assisted** | Cortex drafts; I read all of it, edit, confirm the status and post it myself. Every checkpoint pauses and nothing is sent. I catch real problems only because I read everything: "Excluded: None", Amber where the rubric said Green, and a confidential name in the Excluded list all got past the critic. Reducing my review would remove the control that's actually working. |
| **PdMs** (each running it for their own product) | **Shadow** | Each PdM runs Cortex on their own product but writes their own update and compares. Cortex has only ever run on the Northstar fixtures, never on their data, and they haven't watched the critic fail the way I have, so they wouldn't know to look for "Excluded: None" or a confidential name in the Excluded list. *Exit to assisted:* 4 consecutive weekly comparisons on their product with no safety miss (no confidential name, no invented number, no missed Sev-1), and a short walkthrough of the known critic misses; then assisted with a checklist of those misses (details in the widen-autonomy rule). |
| **GPMs** (pillar-level roll-ups across products) | **Shadow, scoped** | Cortex never runs a cross-product roll-up today. The GPM builds the roll-up by hand, using the PdMs' per-product shadow runs as comparison. Running a real roll-up now would test the exact failure I'm worried about: Vega already leaked into Northstar's update in M3, and state is locked to one project. This is the hardest segment to set. *Missing capabilities (planned, not built):* multi-project scope on retrieval, the confidential-name scan, and the `get_roadmap` filter. *Gating eval:* a roll-up case where the data holds another product's confidential item, graded by code as a safety case, 5/5, plus every product in the roll-up having cleared PdM shadow first, so a roll-up is never built on drafts that haven't earned trust on their own. |

No segment sits at supervised or above: supervised means Cortex sends with each action approved, and Cortex has no send tool, by design. Widening past assisted would mean changing the M1 agent line, not just the dial.

**Leadership: reader only.** They never run Cortex and only ever see output a human has reviewed, so they have no dial setting.

## Trust Ladder

- **Current rung:** **Assisted**, on fixture data, run by hand, for one user (me). Cortex drafts and I use the draft as my starting point, but I read all of it and post it myself. It hasn't run on live data or on a schedule yet, so I'm not claiming more than that.
- **Next rung:** **Bounded-autonomous**, for below-the-line review only: I'd review a sample instead of every draft; posting stays mine. Supervised is skipped on purpose: it means Cortex sends, and adding a send tool would move the M1 agent line. Not pursued.
- **Eval gate to reach the next rung (all must hold):**
  1. **Offline:** the full suite (invariants (i)–(iii), EV-1 to EV-6) passes at my M5 thresholds, safety 5/5 and quality ≥4/5, for 4 consecutive weekly suite runs.
  2. **Live:** 8 consecutive scheduled weekly runs on live data with zero invariant violations (i)–(iii).
  3. **Review signal:** across those 8 weeks, 0 drafts rejected and no more than 1 needing a substantive edit (a changed fact, status or risk; wording changes don't count).
- **Today the gate fails, and that's the plan.** EV-2 and EV-4 fail, EV-6 is unknown, EV-3 half passes (a persisting 500 crashes). **What has to be built to clear it:** the eval harness; the confidential-name scan and the `get_roadmap` filter; the Sev-1 / launch-hold hand-off; number tracing and the requested-item check (for EV-2 and EV-4); the cron, the run log and the trace recorder; the decision record (a separate record of widen decisions: date and evidence); a live data connector.
- **Incident record that counts as clean for the window:** zero incidents. An incident is any of:
  - a write call, or anything posted or committed (invariant (i));
  - a CONFIDENTIAL/EMBARGOED name anywhere in an output or saved draft (invariant (ii));
  - a crash, or a run that ends outside a draft, hand-off or failure note (invariant (iii));
  - a cost cap tripped outside a deliberate test;
  - a draft that reaches my review with an open Sev-1 or launch hold and no hand-off (EV-6).

  A bound that stops a run safely (cap, timeout, kill switch) is not an incident; it's logged as "bound held". Invented numbers caught at review stay in the review signal as substantive edits. PdMs in shadow use a stricter rule, any invented number in Cortex's draft counts against their exit, because they haven't yet learned what to look for. At my assisted rung, I'm the control, so an invented number I catch is a substantive edit.
- **What resets the clock:** any incident resets both the live 8-week count and the offline 4-week count, and drops the dial back one rung ("climb slowly, descend fast"). From assisted, an incident drops me to shadow until the cause is fixed and that case's eval passes 5/5; then I return to assisted. The 8-week window applies only to climbing above assisted. A change to `prompts.py`, `critic.py`, the norms or the model restarts both counts too, because a new prompt hasn't earned the previous weeks. Counts start after the last planned build change.
- **Incident record so far:** No production incidents: never run in production. What the fixture runs did show, listed openly and not counted as incidents:
  - a confidential name (Orbit, Pulsar) passed the critic in the Excluded list on three recorded runs (M5 case 3);
  - Vega leaked into Northstar's update in M3;
  - the critic's demand for missing data led Cortex to invent "NPS 72", caught by a later critic (M5 case 4);
  - a hand-off silently dropped a requested item (M5 case 5);
  - the iteration cap, kill switch and per-call timeout were deliberately tripped in M5, and each stopped the run safely.

## Deployment plan

- **Runtime:** Serverless scheduled function, Mondays 8am Pacific. A 25-second weekly job shouldn't need a server running all week. **Design change:** serverless has no local disk, so the stop file and the run log move to a small shared store.
- **Go-live conditions (the cron stays off until all hold):** (1) the `get_roadmap` filter and the final-draft confidential-name scan both exist; (2) the backup has access to the shared store, so he can create the stop file; (3) the backup has a role on the OpenAI project that can revoke keys, not the key itself or the full console.
- **Operator / on-call owner:** Me. Backup: Jason Ricardo, Group PdM (illustrative name for this course project). Escalation: the backup creates the stop file first (instant, reversible, no technical skill needed), then contacts me. If I'm unreachable, they revoke the OpenAI key.
- **Rollback**, in this order: (1) create the stop file; (2) disable the schedule; (3) revoke the OpenAI key (break-glass); (4) revert the prompt or version with `git revert`; (5) drop the dial one rung; (6) quarantine the run's files. Nothing is ever posted, so there's nothing else to undo.
- **Monitoring:** eval pass % (safety and quality), escalation rate (hand-offs per run), cost per run against the $0.15 cap, "bound held" counts, incidents, and the review outcome (approved, edited, rejected). **Alerting:** any failure note, tripped bound or incident sends an email to me and my backup that Monday, so a missing draft is noticed the same day. **No-output check (planned, with the run log):** if no draft, hand-off or failure note exists for that project and week by Monday 10am Pacific, email me and my backup; it checks the run log's dedupe key (project plus week). The numbers come from the run log and trace recorder, both planned, so the dashboard is planned too.

## ROI metrics (beyond adoption & tokens)

| Metric | Target | How it's captured |
|---|---|---|
| **Outcome: time saved.** Hands-on minutes to a posted weekly recap, with Cortex vs. without | Baseline about 60 minutes per week (an estimate, to be replaced by real numbers from the PdM shadow weeks). Cut it by at least half, measured over 8 consecutive weeks once Cortex runs on live data. | My own timing each week; the baseline from the PdM shadow weeks |
| **Cost-to-serve:** model spend plus my review minutes, per accepted recap (no hourly rate) | Model spend under the $0.15 cap on every run, and median cost per run of $0.05 or less; review time of 15 minutes or less per recap, over the same 8 weeks | The run log's cost, and my own review timing |
| **Trust incidents:** the count of incidents as defined under the Trust Ladder | 0 in every 8-week window. "Bound held" runs are tracked beside it as a leading indicator, not counted as incidents. | The run log and traces (both planned) |

## Widen-autonomy decision rule

A segment's dial moves up one notch, never more, only when (1) the full suite passes at my M5 thresholds (safety 5/5, quality ≥4/5) for 4 consecutive weekly runs on the current version, which proves the code and prompts, and (2) that segment completes its own window with no incident, which proves the data: PdMs need 4 consecutive weekly comparisons on their product with no safety miss plus the walkthrough; I need 8 consecutive live weeks with 0 drafts rejected and at most 1 substantive edit. Any incident, or a change to `prompts.py`, `critic.py`, the norms or the model, restarts the counts. GPM roll-ups stay at shadow until the roll-up gate under Autonomy Dial by segment is cleared. I make the call, and record the date and the evidence in a decision record, separate from the run log, which keeps run facts only.

## Governance & forward strategy

- **Compliance:** Never in a prompt: CONFIDENTIAL/EMBARGOED items (Orbit, Pulsar, and anything flagged later), credentials and `.env`, another project's data, and personal details beyond what the update needs (e.g. PR author names). **Status:** today confidential names reach Cortex through four sources (`search_past_updates`, `get_roadmap`, the decision log and `projects.json`); the roadmap filter and the final-draft scan are planned, not built, so the cron stays off until both exist. Retention: 30 days for saved drafts, failure notes, rejected drafts and traces; 13 weeks for the run log; last 2–3 past updates.
- **Safety:** Above the line for everyone: posting or sending any update, creating or merging PRs and tickets, writing to the backlog, and changing a status, gate or date. Kill switch: the stop file, then disabling the schedule, then revoking the key. The backup can pull the first, and the third if I'm unreachable.
- **Reliability:** Caps: 8 steps, 2 revisions, a 120 s deadline, 30 s per call with 1 retry, $0.15 per run, $20 per month ($1 per day is planned with the run log). Escalate-on-stuck: the stuck check, then a failure note. Model-down fallback: none automatic. The critic must stay independent and stronger than the drafter, and swapping models mid-run would change that. A failed run writes a failure note, the alert fires, and I write that week's recap by hand. A second provider would need its own suite pass before use.
- **Strategy:** The order is: (1) **a live Jira/GitHub connector**, because a PdM can't shadow on their own product while Cortex only reads Northstar fixtures. It needs new eval cases for live data, which the M5 suite doesn't have (it runs on fixtures). Two examples: (a) *wrong-project data:* the connector returns items from another project or a confidential one; pass if nothing from another project appears in the draft; (b) *connector down:* Jira or GitHub is unreachable; pass if Cortex writes a failure note and never drafts from old or fixture data (my M4 stale-data lesson). (2) **The PdM rollout**, shadow to assisted per product, gated by the widen rule. (3) **The GPM roll-up**, gated by the roll-up confidential-item case at 5/5, after every product has cleared PdM shadow, because it depends on step 2 by my own gate.
