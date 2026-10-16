"""Independent validator (M3). A separate model call that never saw the drafting
context, so it can't inherit the draft's blind spots. Returns a pass/fail verdict.
The revision cap that stops a critic<->drafter loop lives in `agent.py`.
"""

from __future__ import annotations

import json

from prompts import CRITIC_LABELS, CRITIC_SYSTEM


def _normalise_reasons(reasons) -> list[dict]:
    """Make every reason {"label": <fixed label>, "detail": str} so code can compare them."""
    out = []
    for r in reasons if isinstance(reasons, list) else []:
        if isinstance(r, dict):
            label, detail = str(r.get("label", "OTHER")), str(r.get("detail", ""))
        else:
            label, detail = "OTHER", str(r)
        out.append({"label": label if label in CRITIC_LABELS else "OTHER",
                    "detail": detail})
    return out


def review(client, model: str, proposed_output: str, source_data: str) -> dict:
    """Return {"verdict": "pass"|"fail", "reasons": [{"label", "detail"}]} for a proposed output."""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CRITIC_SYSTEM},
            {"role": "user", "content":
                f"SOURCE DATA Cortex used:\n{source_data}\n\n"
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
    verdict["_usage"] = {"prompt": usage.prompt_tokens, "completion": usage.completion_tokens}
    return verdict
