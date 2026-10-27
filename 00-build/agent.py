"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the run
deadline and per-call timeout, the stop/escalate conditions, the auto-queue cap,
and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Every run ends one of three ways, saved to run-output/ and never posted (there is no
publish tool): a FINAL STATUS UPDATE draft, a HAND-OFF draft marked NOT COMPLETE with
the items that need a human decision, or a short failure note when Cortex gives up.

Requires OPENAI_API_KEY in your environment (see .env.example). Model and bounds
are read from env so you can tune them, that tuning is your M5 deliverable.

The loop is deliberately transparent (hand-written tool-calling on the openai
client) so a grader can see the machinery. Keep the bounds explicit if you rework it.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from openai import APITimeoutError, OpenAI

import tools
from critic import review
from prompts import CORTEX_SYSTEM, OPPOSITE_PAIRS

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds (your M5 deliverable: tune these and justify them) ----------------
MODEL = os.environ.get("CORTEX_MODEL", "gpt-4o-mini")
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.15"))
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))
# Timeouts, in seconds. The loop checks the run deadline before each step. The
# per-call timeout is set on the client, because a hung call never returns to the loop.
RUN_DEADLINE_S = float(os.environ.get("CORTEX_RUN_DEADLINE_S", "120"))
CALL_TIMEOUT_S = float(os.environ.get("CORTEX_CALL_TIMEOUT_S", "30"))
CALL_RETRIES = int(os.environ.get("CORTEX_CALL_RETRIES", "1"))
# Kill switch: if this file exists, the loop halts at its next step. Cortex has no
# file-write tool and the code only writes to run-output/, so Cortex can't remove it.
STOP_FILE = Path(__file__).parent / "STOP"
# Rough $ per 1M tokens for your chosen model, set to match its pricing.
PRICE_IN = float(os.environ.get("CORTEX_PRICE_IN_PER_M", "0.15"))
PRICE_OUT = float(os.environ.get("CORTEX_PRICE_OUT_PER_M", "0.60"))
# The critic runs on a stronger model than the drafter (M1 agent line map), costed at
# its own price so the cost cap sees the real spend.
CRITIC_MODEL = os.environ.get("CORTEX_CRITIC_MODEL", "gpt-4o")
CRITIC_PRICE_IN = float(os.environ.get("CORTEX_CRITIC_PRICE_IN_PER_M", "2.50"))
CRITIC_PRICE_OUT = float(os.environ.get("CORTEX_CRITIC_PRICE_OUT_PER_M", "10.00"))

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_project", "description": "Look up a project by its ID (status, flags, linked PRD).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "get_activity",
        "description": "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "search_past_updates",
        "description": "Search previous status updates and decisions for tone and precedent.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_roadmap",
        "description": "Return the roadmap. Some items are flagged confidential/embargoed.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_norms", "description": "Return the team norms / PM playbook the agent must follow.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "propose_stories",
        "description": "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"},
            "stories": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"}}, "required": ["project_id", "stories"]}}},
]


class Bounds:
    """Tracks spend and trips the cost cap. This is enforced OUTSIDE the model."""

    def __init__(self):
        self.cost = 0.0

    def add(self, usage) -> None:
        self.cost += (usage.prompt_tokens * PRICE_IN
                      + usage.completion_tokens * PRICE_OUT) / 1_000_000

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


OUTPUT_DIR = Path(__file__).parent / "run-output"


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def _save(name: str, text: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / name
    out.write_text(text, encoding="utf-8")
    print(f"\nSaved -> {out.relative_to(Path(__file__).parent)}  (nothing was posted)")


# Three kinds of outcome (loop-spec.md section 3). Nothing here posts or sends anything.
#   emit_draft    success: a complete, critic-passed recap draft, held for the PM.
#   emit_handoff  escalate: a draft with blocked items, clearly NOT COMPLETE.
#   give_up       stuck: a short failure note. It is not a draft.
# Only drafts and hand-offs (status-update-*.md) count as the week's draft. A failure
# note or rejected draft never does, and Cortex never reads run-output/ as a source.

def emit_draft(which: str, draft: str, cost: float) -> None:
    banner("FINAL STATUS UPDATE (draft, validator-approved, NOT posted)")
    print(draft.rstrip())
    _save(f"status-update-{which}.md",
          f"<!-- Cortex draft, accepted by validator; NOT posted. "
          f"Run cost ~ ${cost:.4f}. -->\n\n{draft.rstrip()}\n")


def emit_handoff(which: str, draft: str, blocked: list[str], cost: float) -> None:
    items = blocked or ["Cortex could not draft this and escalated (see below)"]
    banner(f"HAND-OFF, NOT COMPLETE: {len(items)} item(s) need your decision. "
           f"Nothing posted. Run cost ≈ ${cost:.4f}")
    for item in items:
        print(f"  NEEDS YOUR DECISION: {item}")
    print()
    print(draft.rstrip())
    top = "".join(f"**NOT COMPLETE, NEEDS YOUR DECISION:** {i}\n" for i in items)
    _save(f"status-update-{which}.md",
          f"{top}\n<!-- Cortex hand-off draft; NOT posted. Run cost ~ ${cost:.4f}. -->\n\n"
          f"{draft.rstrip()}\n")


def give_up(which: str, reason: str, last_draft: str, cost: float,
            rerun_helps: bool = True, advice: str | None = None) -> None:
    """Stop and say why. A short failure note, not a draft. A rejected draft, if any, is
    saved in its own clearly labelled file; it is never the week's draft.
    rerun_helps=False is for a cause a rerun cannot fix (project not found); advice
    overrides the default line for any other cause (the kill switch)."""
    banner(f"GAVE UP, short failure note (not a draft). Nothing posted. "
           f"Run cost ≈ ${cost:.4f}")
    advice = advice or ("A rerun can try again." if rerun_helps else
                        "Check the project ID. A rerun won't help until it's corrected.")
    note = (f"# Failure note: Cortex could not finish ({which})\n\n"
            f"**Why:** {reason}\n\n"
            f"No recap draft was produced. {advice} "
            f"Nothing was posted or sent. Run cost ~ ${cost:.4f}.\n")
    print(note)
    _save(f"failure-note-{which}.md", note)
    if last_draft.strip():
        _save(f"rejected-draft-{which}.md",
              "**REJECTED DRAFT, do not use or forward.**\n"
              "Not the week's draft. Cortex never reads this file as a source.\n\n"
              f"<!-- Rejected because: {reason} -->\n\n{last_draft.rstrip()}\n")


# Tools that DO something (queue stories) rather than read a source. They are left out
# of part 4's "Used" list; the queued stories already appear in part 6.
ACTION_TOOLS = {"propose_stories"}

# The six parts of "done" (loop-spec.md section 2). Checked in code, not only by the critic.
SIX_PARTS = (  # (number, title, key word the heading must contain)
    ("1", "Proposed status", "status"), ("2", "What got done", "done"),
    ("3", "Risks and issues", "risks"), ("4", "Sources used and excluded", "sources"),
    ("5", "Risks considered but not flagged", "considered"),
    ("6", "Proposed stories", "stories"),
)


def _part_heading(num: str, keyword: str) -> re.Pattern:
    """A heading line (starts with # or **) with the part number and its key word.
    Tolerant of formatting slips (heading level, bold, separator, wording); a missing
    section still has no matching heading line, so it still fails."""
    return re.compile(
        rf"^(?:#{{1,6}}\s*|\*\*\s*){num}\s*[.):\-]\s*[^\n]*?{keyword}[^\n]*$", re.M | re.I)


def missing_parts(text: str) -> list[str]:
    """Names of the six parts missing from a DONE draft. An ESCALATE note has no parts."""
    if re.search(r"^\s*ESCALATE:", text, re.M):
        return []
    return [f"{n}. {t}" for n, t, k in SIX_PARTS if not _part_heading(n, k).search(text)]


def blocked_items(text: str) -> list[str]:
    """Items Cortex marked 'NEEDS YOUR DECISION: ...' (a hand-off draft)."""
    return [m.strip() for m in re.findall(r"NEEDS YOUR DECISION:\s*(.+)", text)]


def is_escalation(text: str) -> bool:
    return bool(re.search(r"^\s*ESCALATE:", text, re.M))


# Hand-off trigger (loop-spec.md section 3): the REQUEST asks for a date. A date the
# draft volunteers is judged by the critic (regex on dates would also catch merge dates).
DATE_ASK = re.compile(
    r"\b(?:GA|launch|ship|release|go-live)\s+date\b|\bfirm\s+(?:launch\s+|ship\s+)?date\b",
    re.I)


def _same_item(x: str, y: str) -> bool:
    """Two reasons point at the same item. If either has no item, assume they might (the
    old behaviour), so a critic that skips "item" can still be caught as stuck."""
    return not x or not y or x == y


def stuck_reason(prior: set[tuple[str, str]], current: set[tuple[str, str]]) -> str:
    """Stuck (loop-spec.md section 3): opposite critic reasons about the SAME item, or
    the same reason back after a revision. Reasons are (label, item) pairs; OTHER and OK
    are not specific, so ignored."""
    ignore = {"OTHER", "OK"}
    cur = {r for r in current if r[0] not in ignore}
    pri = {r for r in prior if r[0] not in ignore}

    def opposed(xs, ys, a, b):
        return any(l1 == a and l2 == b and _same_item(i1, i2)
                   for l1, i1 in xs for l2, i2 in ys)

    for a, b in OPPOSITE_PAIRS:
        if opposed(cur, cur, a, b) or opposed(pri, cur, a, b) or opposed(pri, cur, b, a):
            return f"the critic asked for opposite changes ({a} and {b}); no revision can pass"
    again = sorted({l for l, _ in cur} & {l for l, _ in pri})
    if again:
        return f"the same critic reason came back after a revision ({', '.join(again)})"
    return ""


def add_used_sources(text: str, calls: list[str]) -> str:
    """Insert the 'Used' list under part 4 from the REAL tool calls, so it can't be wrong."""
    used = "\n".join(f"- {c}" for c in calls) or "- (no tools were called)"
    block = f"\n**Used (from the actual tool calls):**\n{used}\n"
    return _part_heading("4", "sources").sub(
        lambda m: m.group(0) + block, text, count=1)


def run(which: str = "happy") -> None:
    client = OpenAI(timeout=CALL_TIMEOUT_S, max_retries=CALL_RETRIES)
    bounds = Bounds()
    started = time.monotonic()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    banner(f"CORTEX RUN, fixture: task-{which}  (auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(task["body"])

    messages = [
        {"role": "system", "content": CORTEX_SYSTEM},
        {"role": "user", "content": f"PM task brief:\n\n{task['body']}"},
    ]
    source_log: list[str] = [task["body"]]
    calls_made: list[str] = []  # real tool calls, used to write part 4's "Used" list
    revisions = 0
    last_draft = ""
    prior_labels: set[tuple[str, str]] = set()  # (label, item) from earlier rejections
    date_asked = bool(DATE_ASK.search(task["body"]))

    for step in range(1, MAX_ITERATIONS + 1):
        if STOP_FILE.exists():
            give_up(which, "halted by kill switch (00-build/STOP exists)", last_draft,
                    bounds.cost, advice="Delete 00-build/STOP to resume; a rerun "
                    "halts until then.")
            return

        if bounds.over_cap():
            give_up(which, f"cost cap ${COST_CAP_USD} hit at ${bounds.cost:.4f}",
                    last_draft, bounds.cost)
            return

        elapsed = time.monotonic() - started
        if elapsed >= RUN_DEADLINE_S:
            give_up(which, f"run deadline {RUN_DEADLINE_S:.0f}s hit at {elapsed:.0f}s",
                    last_draft, bounds.cost)
            return

        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
        except APITimeoutError:
            give_up(which, f"model call timed out ({CALL_TIMEOUT_S:.0f}s per call, "
                    f"{CALL_RETRIES} retry)", last_draft, bounds.cost)
            return
        bounds.add(resp.usage)
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for call in msg.tool_calls:
                fn = call.function.name
                args = json.loads(call.function.arguments or "{}")
                result = tools.TOOLS[fn](**args)
                source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
                label = f"{fn}({', '.join(f'{k}={v}' for k, v in args.items())})"
                if fn not in ACTION_TOOLS and label not in calls_made:
                    calls_made.append(label)  # sources only; actions are not sources
                print(f"\n[step {step}] TOOL {fn}({args})")
                print(f"          -> {json.dumps(result)[:300]}")
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result)})
                if isinstance(result, dict) and result.get("error") == "project_not_found":
                    # Hard stop, enforced in code: never retry, never substitute another
                    # project (the error lists other projects; Cortex must not pivot).
                    give_up(which, f"project not found: {result.get('project_id') or args}",
                            "", bounds.cost, rerun_helps=False)
                    return
            continue

        # No tool calls => Cortex produced a proposed output. Validate it.
        proposed = msg.content or ""
        missing = missing_parts(proposed)
        if not missing:
            proposed = add_used_sources(proposed, calls_made)
        last_draft = proposed
        print(f"\n[step {step}] PROPOSED OUTPUT:\n{proposed}")

        date_unmarked = (date_asked and not missing and not is_escalation(proposed)
                         and not any("date" in b.lower() for b in blocked_items(proposed)))
        if missing:
            # Completeness check in code: "done" needs all six parts. No critic call.
            banner("COMPLETENESS CHECK, code (no critic call)")
            verdict = {"verdict": "fail", "reasons": [
                {"label": "MISSING_PART", "detail": f"missing part(s): {', '.join(missing)}"}]}
        elif date_unmarked:
            # The request asks for a date: Cortex must hand that item off, not answer it.
            banner("DATE CHECK, code (no critic call)")
            verdict = {"verdict": "fail", "reasons": [
                {"label": "NORMS_VIOLATION", "detail": "the request asks for a date; "
                 "mark it 'NEEDS YOUR DECISION: <date>' and leave the date out"}]}
        else:
            banner("CRITIC, independent validation")
            # The norms come from code, so the rubric never depends on what Cortex pulled.
            try:
                verdict = review(client, CRITIC_MODEL, proposed, "\n".join(source_log),
                                 norms=tools.get_norms()["norms"])
            except APITimeoutError:
                give_up(which, f"critic call timed out ({CALL_TIMEOUT_S:.0f}s per call, "
                        f"{CALL_RETRIES} retry)", last_draft, bounds.cost)
                return
            # Estimate critic spend too, at the critic model's own price.
            bounds.cost += (verdict["_usage"]["prompt"] * CRITIC_PRICE_IN
                            + verdict["_usage"]["completion"] * CRITIC_PRICE_OUT) / 1_000_000
        print(json.dumps({k: v for k, v in verdict.items() if k != "_usage"}, indent=2))

        if verdict["verdict"] == "pass":
            blocked = blocked_items(proposed)
            if blocked or is_escalation(proposed):
                emit_handoff(which, proposed, blocked, bounds.cost)
            else:
                banner(f"HITL CHECKPOINT, status update + any proposed stories queued for "
                       f"your review. Nothing posted, no commitments made. "
                       f"Run cost ≈ ${bounds.cost:.4f}")
                emit_draft(which, proposed, bounds.cost)
            return

        # Stuck check, before the revision cap: stop early and say why.
        labels = {(r["label"], r.get("item", "")) for r in verdict["reasons"]}
        stuck = stuck_reason(prior_labels, labels)
        prior_labels |= labels
        if stuck:
            give_up(which, f"stuck: {stuck}", last_draft, bounds.cost)
            return

        if revisions >= MAX_REVISIONS:
            give_up(which, f"revision limit: rejected {MAX_REVISIONS + 1}x "
                    f"({MAX_REVISIONS} revisions used)", last_draft, bounds.cost)
            return

        revisions += 1
        print(f"\n-> rejected; revision {revisions}/{MAX_REVISIONS}")
        messages.append(msg)
        messages.append({"role": "user", "content":
                         "A validator rejected that for these reasons: "
                         + "; ".join(f"{r['label']}: {r['detail']}" for r in verdict["reasons"])
                         + ". Fix it."})

    give_up(which, f"max iterations ({MAX_ITERATIONS}) reached", last_draft, bounds.cost)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "happy")
