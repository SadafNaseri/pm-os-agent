"""Forced test for the M2 stuck check. It does NOT change critic.py or any prompt.

It runs the real Cortex loop but swaps in a scripted fake critic that rejects with
chosen labels, so you can watch the stuck exit fire without waiting for the real
critic to contradict itself. Cortex still drafts with the real model (a few cents).
Output goes to run-output/forced-<case>/ so it never overwrites a real run.

Usage:
    python3 forced_stuck_test.py opposite   # STATUS_TOO_HIGH, then STATUS_TOO_LOW
    python3 forced_stuck_test.py repeat     # UNSUPPORTED_CONTENT, twice
Expected: the run gives up with "stuck: ..." after the second rejection, before the
revision cap, and writes a failure note plus a clearly labelled rejected draft.
"""

from __future__ import annotations

import sys

import agent

CASES = {
    "opposite": [["STATUS_TOO_HIGH"], ["STATUS_TOO_LOW"]],
    "repeat": [["UNSUPPORTED_CONTENT"], ["UNSUPPORTED_CONTENT"]],
}


def scripted_critic(script):
    calls = {"n": 0}

    def fake_review(client, model, proposed_output, source_data):
        labels = script[min(calls["n"], len(script) - 1)]
        calls["n"] += 1
        return {"verdict": "fail",
                "reasons": [{"label": l, "detail": "forced by test"} for l in labels],
                "_usage": {"prompt": 0, "completion": 0}}

    return fake_review


if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else ""
    if case not in CASES:
        sys.exit(f"usage: python3 forced_stuck_test.py {{{'|'.join(CASES)}}}")
    agent.review = scripted_critic(CASES[case])
    agent.OUTPUT_DIR = agent.OUTPUT_DIR / f"forced-{case}"
    agent.run("happy")
