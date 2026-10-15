# Step 4 build changes (running list, scratch)

Make the build match the spec's definition of done (§2). Gaps found so far:

1. Part 4 (sources used / excluded) is not produced by the build yet. Add it.
2. Part 5 (risks considered but not flagged) is not produced by the build yet. Add it.
3. The build still says "Yellow". Change to "Amber" (Green / Amber / Red).
4. Fix the contradictory critic rule (Green fails for hiding the open issue; Yellow fails for lacking a Sev-1). Raised by learner in Step 2.

Added in Step 2, Decision 2 (stuck conditions):
5. The critic must report rejection reasons as fixed labels, so the code can compare them.
6. Stuck detection: stop after 2 revisions, or earlier if the critic's rejections ask for opposite changes, or if the same reason comes back after a revision. Stop and tell the learner why. (Build today has only the revision cap of 2 in agent.py:49, 205.)
7. "No data after 3 tries, temporary failures only": no retry logic found in the build. Add it.
8. Project not found = hard stop, never substitute another project (the build pivoted to P-NORTH in the missing-data run).

Added in Step 2, Decision 3 (escalate):
9. Hand-off draft: mark each blocked item clearly ("needs your decision: GA date"), leave out the part Cortex can't decide, and never let a draft with a blocked part look complete when skimmed.
10. Hand-off trigger: any open Sev-1 or launch hold = hand off (replaces "unsure whether to escalate a risk"). Lower risks still appear in part 5 of every draft.
11. Hand-off triggers to check in code: draft or request commits to a date or "Green"; stories over the cap of 10; notes contain instructions to post or share.

Added in Step 2 (Green trigger narrowed):
12. Label the status "proposed" in every draft (Green / Amber / Red); the learner confirms it at review. "Green" is no longer a hand-off trigger. Check that the build's norms/critic don't still treat Green as a block.
    Note: spec §2 part 1 doesn't mention "proposed"; §3 has the rule.

Added in Step 3 (state):
13. Run log (planned unless we build it in Step 4): one log per project, one line per run with week covered, outcome (draft / hand-off / failure note / skipped "already drafted") and stop reason. Dedupe key is project plus week. Run facts only, never draft content or claims. Cortex reads it only to check for duplicates, never as draft source material. Only real recap drafts and hand-off drafts count for dedupe; failure notes don't.

Already in the build, no change needed: $0.50 cost cap (agent.py:50, 160) and revision cap of 2 (agent.py:49, 205).

Added at the start of Step 4:
14. Give-up output: a give-up is a short failure note that does not look like a draft (today the build prints "validator-approved ... queued for review").
15. Six-parts completeness check in code, so "all six parts present" is detectable and not only judged by the critic.

## Decisions (learner, Step 4)
- Build: 1-6, 8, 9, 11 (date trigger only), 12, 14, 15.
- Planned, not built: 7 (3-tries retry), 10 (Sev-1 / launch-hold hand-off), 13 (run log and dedupe). Mark as planned in the spec.
- Item 6: build it and show it firing with a forced test that does not permanently change the critic.
- Leave the existing caps alone ($0.50 cost cap, 2 revisions, story cap).
- Batches, each needing a yes first, diff shown after:
  - Batch 1: items 3, 4, 12 (status wording and norms). Item 4: show old and new norms side by side before changing. The fix makes the rules consistent; it must not make the critic easier to pass.
  - Batch 2: items 1, 2, 5, 15 (the six parts and the completeness check).
  - Batch 3: items 6, 8, 9, 11, 14 (stuck, hard stop, hand-off and the failure note).
