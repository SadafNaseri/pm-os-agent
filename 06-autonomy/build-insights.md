# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 4, what you learned building it
>
> ✅ **What this validates:** you can reflect on what building it taught you, by the end you'll have proven the friction, the learning, and the aha that changes how you'd design your next agent.

## Friction

The build fought me hardest where I trusted instructions to hold. "Never name a confidential project" was a prompt rule, and Orbit and Pulsar still showed up in my Excluded list on three recorded runs (M5 case 3). Each time I tightened the wording and assumed it was fixed, and each time a later run proved me wrong. It cost me several runs and a wrong assumption I kept repeating: that a clearer prompt is a safer prompt.

The other fight was my own critic. When I asked for metrics that weren't in the data, it rejected the draft for leaving them out, and Cortex responded by inventing "NPS 72." The checker I'd built to stop fabrication caused one. That one surprised me most, because I'd been treating the critic as the safe part of the system.

The plain mechanics fought me too: as someone new to the terminal, small things like editing a hidden .env file or pasting an API key cost me real time, and one screenshot exposed my key, so I had to rotate it. That taught me to treat secrets and tooling as part of the design, not an afterthought.

## Learning

1. **If a rule really matters, enforce it in code, not in a prompt.** Every code check I saw run held every time; every rule I only wrote as an instruction held some of the time. The confidential-name rule taught me that the hard way, while the iteration cap, kill switch and timeout stopped runs exactly when they should.
2. **The most dangerous failures are the ones a reviewer can't see.** An invented number is visible if you check it. A missing source, a dropped request or an unescalated risk isn't, because there's nothing on the page to catch. "Excluded: None" and the silently dropped WAU taught me to design for what the agent leaves out, not just what it says.
3. **A checker is only as good as what it can see, and it can cause the failures it's meant to catch.** When I withheld this week's activity, my critic passed last week's news, because it only checks against what the agent pulled. And when it demanded data that didn't exist, it pushed Cortex into inventing "NPS 72." Independence isn't just a separate model; it's a separate view of the truth.

## Aha moment

The riskiest thing an agent does is what it quietly leaves out. I saw it first in Module 1, when my hardest call was that a missed source is invisible in a draft, and it kept coming back: "Excluded: None," a dropped WAU request, and a Sev-1 hand-off I knew I needed but still haven't built. None of those were visible by reading the output, because the problem wasn't on the page.

Next time, I'd design every agent to show its omissions from day one, not just its answer: what it pulled, what it used and what it left out, checked by code that compares what was pulled against what was cited. I'd treat "nothing left out" as a claim to verify, never as a default.

## What you'd do differently

If I rebuilt Cortex from scratch:

1. **Build the eval harness first, not last.** I logged seven real failures across three modules (M2 to M4) before I had anywhere to test them. If the harness and invariants had existed from Module 2, every prompt change would have been checked against my past failures automatically, instead of me noticing them run by run.
2. **Put the confidential-name check in code on day one.** I spent two rounds tightening a prompt rule that never fully held. A simple code scan of the draft against the flagged names would have taken less time than either of those rounds, and it would have actually worked.
3. **Settle secrets and the critic's inputs before the first run.** I'd create a restricted API key from the start and never open .env on screen, instead of rotating the key mid-course. And I'd give the critic its own copy of the norms from the first run, not from Module 3, so it never judged status without the rubric.
