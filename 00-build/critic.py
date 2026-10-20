"""Independent validator (M3). A separate model call that never saw the drafting
context, so it can't inherit the draft's blind spots. Returns a pass/fail verdict.
The revision cap that stops a critic<->drafter loop lives in `agent.py`.
"""

from __future__ import annotations

import json

from prompts import CRITIC_LABELS, CRITIC_SYSTEM


def _normalise_reasons(reasons) -> list[dict]:
    """Make every reason {"label": <fixed label>, "item": str, "detail": str} so code can
    compare them. "item" is what the reason is about ("" when the critic didn't say)."""
    out = []
    for r in reasons if isinstance(reasons, list) else []:
        if isinstance(r, dict):
            label, detail = str(r.get("label", "OTHER")), str(r.get("detail", ""))
            item = str(r.get("item", "")).strip().lower()
        else:
            label, detail, item = "OTHER", str(r), ""
        out.append({"label": label if label in CRITIC_LABELS else "OTHER",
                    "item": item, "detail": detail})
    return out


STATUS_ORDER = {"red": 0, "amber": 1, "green": 2}  # higher = better


STATUS_LABELS = ("STATUS_TOO_HIGH", "STATUS_TOO_LOW")


def _derive_status_labels(verdict: dict) -> None:
    """The code, not the model, sets the direction of a status reason. The critic names
    the rubric's status and the proposed status; HIGH/LOW follows from Red < Amber < Green.
    If the two statuses differ, the verdict is forced to fail with a status reason, even
    if the critic said pass: this only enforces the critic's own fields, it does not judge
    status itself. If either status is missing or not a status, nothing here applies and
    the critic's own labels and verdict stand."""
    rubric = STATUS_ORDER.get(str(verdict.get("rubric_status", "")).strip().lower())
    proposed = STATUS_ORDER.get(str(verdict.get("proposed_status", "")).strip().lower())
    if rubric is None or proposed is None:
        return
    for r in verdict["reasons"]:
        if r["label"] not in STATUS_LABELS:
            continue
        # Equal statuses leave no direction to name, so the label becomes OTHER.
        derived = ("STATUS_TOO_HIGH" if proposed > rubric else
                   "STATUS_TOO_LOW" if proposed < rubric else "OTHER")
        if derived != r["label"]:
            r["detail"] += (f" [label changed by code from {r['label']}: rubric "
                            f"{verdict['rubric_status']}, proposed {verdict['proposed_status']}]")
            r["label"] = derived
    if proposed != rubric and not any(r["label"] in STATUS_LABELS for r in verdict["reasons"]):
        verdict["reasons"].append({
            "label": "STATUS_TOO_HIGH" if proposed > rubric else "STATUS_TOO_LOW",
            "item": "status",
            "detail": (f"added by code: the critic's own fields disagree (rubric "
                       f"{verdict['rubric_status']}, proposed {verdict['proposed_status']}); "
                       f"the proposed status must match the rubric")})
    if proposed != rubric:
        verdict["verdict"] = "fail"


def review(client, model: str, proposed_output: str, source_data: str,
           norms: str = "") -> dict:
    """Return {"verdict": "pass"|"fail", "reasons": [{"label", "item", "detail"}]} for a
    proposed output. `norms` is always supplied by the code, whatever Cortex looked up."""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CRITIC_SYSTEM},
            {"role": "user", "content":
                f"SOURCE DATA Cortex used:\n{source_data}\n\n"
                f"TEAM NORMS (always supplied):\n{norms}\n\n"
                f"CORTEX PROPOSED OUTPUT:\n{proposed_output}"},
        ],
        response_format={"type": "json_object"},
    )
    usage = resp.usage
    try:
        verdict = json.loads(resp.choices[0].message.content)
    except (json.JSONDecodeError, TypeError):
        verdict = {"verdict": "fail", "reasons": ["critic returned unparseable output"]}
    verdict["reasons"] = _normalise_reasons(verdict.get("reasons"))
    _derive_status_labels(verdict)
    verdict["_usage"] = {"prompt": usage.prompt_tokens, "completion": usage.completion_tokens}
    return verdict
