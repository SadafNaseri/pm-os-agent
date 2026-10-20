"""Forced test for the critic (M3): inject a fault into a real Cortex draft.

It does NOT change critic.py or any prompt. Cortex drafts normally on the real model.
On the FIRST critic call only, this script edits the draft before the real critic sees
it: it changes the activation rate from 41% to 47% and adds an invented metric line
(weekly active users and NPS, neither of which is in the pulled data). The real critic
then reviews the tampered text, so you can watch it reject a bad draft and the
fail-action fire (revise, up to the cap). Output goes to run-output/forced-tamper/ so
it never overwrites a real run.

Honest caveat: Cortex is then asked to fix numbers it did not write, so it will most
likely resubmit its original draft. Caption any screenshot as an injected fault: "draft
edited before the critic".

Usage:
    python3 forced_tamper_test.py
Expected: verdict "fail" with UNSUPPORTED_CONTENT (and maybe others) naming the injected
figures, then "-> rejected; revision 1/2", then a second review of Cortex's own draft.
"""

from __future__ import annotations

import re

import agent
from critic import review as real_review

INVENTED_LINE = "- Weekly active users up 12% week-over-week; NPS 62."


def tamper(text: str) -> str:
    """Change one real figure and add one invented metric line under part 2."""
    text = text.replace("41%", "47%")
    return re.sub(r"(##\s*2\.[^\n]*\n)", lambda m: m.group(1) + INVENTED_LINE + "\n",
                  text, count=1)


def tampering_review(client, model, proposed_output, source_data, norms=""):
    tampering_review.calls += 1
    if tampering_review.calls == 1:
        bad = tamper(proposed_output)
        agent.banner("INJECTED FAULT (test script): draft edited before the critic sees it")
        print("  41% -> 47% (activation rate)\n"
              f"  added under part 2: {INVENTED_LINE}\n"
              "  (neither 47%, weekly active users nor NPS is in the pulled data)")
        proposed_output = bad
    return real_review(client, model, proposed_output, source_data, norms=norms)


tampering_review.calls = 0


if __name__ == "__main__":
    agent.review = tampering_review
    agent.OUTPUT_DIR = agent.OUTPUT_DIR / "forced-tamper"
    agent.run("happy")
