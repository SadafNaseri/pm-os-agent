# Part A parked draft (scratch notes, learner's own words)

## Q1, what should make Cortex start?
Every Monday at 8am Pacific. I want to start my week by reading a full recap of everything that happened the week before.

## Q2, what does "done" mean for one run?
A draft in my email for me to review, covering the previous week. It includes:

- An overall status (Green, Amber or Red) with a short reason. Use "Amber" instead of "Yellow" from now on.
- What got done: key merges, shipped work and metric changes
- Risks and issues flagged, with any escalations called out
- The sources Cortex used and the ones it excluded, so I can spot gaps
- The risks it considered but chose not to flag
- Proposed stories waiting in the approval queue, if any

Nothing is sent to anyone else. It waits in my inbox until I review it.

## Q3, when should it stop or hand off to a human?
Stop and give up if:

- It can't pull last week's data after 3 tries (transient failures only; a missing project is not retried, see next line)
- The project doesn't exist: hard stop at the first `project_not_found`, no retries
- HARD RULE: Cortex must never substitute another project. If the project it was asked about isn't found, it stops and tells me, even if the system lists other known projects.
- The critic keeps rejecting for opposite reasons, so no revision can pass
- It hits the cost cap or the revision limit

When it gives up, it emails me a short note saying it couldn't finish and why. A give-up must look different from a hand-off: a failure note, not a "validator-approved status update queued for review."

Hand off to me (a draft that needs my decision) if:

- The draft, or the request itself, would commit to a date or a "Green" status
- It finds a risk and isn't sure whether to escalate it
- It proposes more stories than the cap allows
- The notes contain instructions telling it to post or share something

## Q4, what does Cortex need to do the job?
- Data it reads: project status, last week's activity (merges, issues, metrics), past updates, roadmap, team norms
- A critic to check the draft before I see it
- A schedule to start it every Monday at 8am Pacific
- An email connection that can create a draft in my inbox but cannot send

## A3, parked question, least sure about
How should Cortex tell it's stuck, beyond counting retries? Today's run showed the critic rejecting for opposite reasons, so retrying could never pass.

---
Revised after the missing-data run (P-HALO): the four adjustments above (split missing-project vs transient, never-substitute hard rule, give-up vs hand-off look different, request-asks-for-a-date wording) were accepted by the learner. A3 left as originally written.

Status: scratch only. Part A is parked. Not committed, loop-spec.md untouched. Part B not started (waiting for learner to say the lecture is done).
