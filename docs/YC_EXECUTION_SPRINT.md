# Kernellum: from research assets to a testable company

Decision date: 28 September 2026. This is an execution plan and draft application
material, not an assertion of YC readiness, acceptance, revenue or traction.

## Decision

Keep Kernellum's broad research mission. Concentrate the next commercial sprint
on one task: helping accelerator engineers make architecture decisions from
their routing evidence. Use Route Review as a small testable starting point.
Do not wait for a field-level breakthrough before talking to users or applying.

The existing work provides implementation credibility. It does not yet establish
a repeatable business. No confirmed external usage, customer interviews, paid
pilots or revenue were found in the materials reviewed for this sprint. Record
these as **unverified**, not invented zeros or hypothetical successes.

Do not spend this sprint on another branding cycle, a new general-purpose agent
platform, additional B-local seed sweeps, or training a foundation model. The
B-local closure is a substantive negative finding and remains closed.

## First customer hypothesis

**User:** an FPGA accelerator engineer repeatedly comparing tiled GEMM variants.
**Potential buyer:** an engineering lead at a small accelerator or FPGA design
team that owns the design schedule. Academic engineers can test usability but
their approval alone is not commercial validation.
**Moment of need:** after several candidate implementations finish, before the
team commits further routing time or a design review to one architecture.
**Job:** determine which candidate meets resource limits and improves the target
workload, identify failed attempts, and provide a reproducible explanation.

The initial K1/ECP5 scope is too narrow to establish a venture-scale market by
itself. It is an inexpensive test surface. Expansion into other flows is justified
only when a real team supplies an adjacent task and commits to evaluating it.
Our inference is that workflow value may be more reachable than new silicon IP
under the current no-hardware-purchase, no-paid-API constraint. Demand is unknown.

### Product versus current implementation

| Capability | Current status | Next evidence needed |
| --- | --- | --- |
| Compare existing K1 routes for arbitrary positive GEMM dimensions | Implemented in engineering preview | External unaided use on compatible inputs |
| Apply resource limits and explain exclusions | Implemented | Engineer verifies classifications |
| Export report and input provenance | Implemented | Report accepted in an actual design decision |
| Reduce engineer analysis time | Hypothesis | Timed comparison with their existing workflow |
| Choose fewer future route evaluations | Earlier bounded K1 research; not a feature of this preview | Customer-defined prospective equal-budget comparison |
| Ingest arbitrary RTL, vendor tools or ASIC flows | Not supported | Scope, adapter, equivalence and provenance tests |
| Improve deployed hardware performance | Not established | Relevant hardware or deployment measurement |

The first pilot offer: **bring one in-scope workload, a baseline and compatible
route records; receive a reproducible constrained comparison and help identifying
the next engineering question.** This is an assisted engineering pilot, not a
promise of faster chips or tapeout-ready designs.

## Competitive reality

The minimum baseline is the engineer's existing CSV notebook or spreadsheet,
not random search. A reporting tool that cannot beat that workflow has no reason
to exist as a paid product. Existing EDA tools, scripts and in-house expertise
are also alternatives.

YC's company pages describe Silimate as chip design/debug agents and Silogy as
a chip simulation/debug platform. ChipAgents publicly offers an agentic chip
design environment; SiliconCompiler offers an open source hardware build system.
These are adjacent capabilities, not proof that our narrow workflow is already
solved or uniquely unsolved. Do not say Kernellum has no competitors.

Our proposed entry point is a smaller, inspectable architecture decision workflow
with supplied evidence and explicit failure accounting. That positioning is a
hypothesis, not a defensible moat. Durable value would require repeated workflow
adoption, deeper integrations, and a permissioned record of which search decisions
transfer across customer workloads. Publishing reports alone does not create it.

## Fourteen-day sprint: 29 September to 12 October

These targets are internal decision gates, not YC admission requirements.
The founder owns outreach and customer discussions. Engineering work can be
performed in active assistant sessions; this document does not start a background
worker or promise continuous execution.

| Dates | Deliverable | Owner | Acceptance evidence |
| --- | --- | --- | --- |
| 29–30 Sep | Identify 20 relevant teams; seek 10 short workflow interviews | Founder, with research assistance | Each prospect has an actual FPGA/accelerator project, a matching engineer role and a reason to care |
| 29 Sep–2 Oct | Conduct interviews using the script below | Founder | Last real incident, current workaround, frequency, consequence and decision owner recorded |
| 1–4 Oct | Obtain 3 permissioned example tasks and observe first use | Founder + engineering | Input package, baseline, agreed task and completion record; sample data alone is not a pilot commitment |
| 3–7 Oct | Fix the largest repeated blocker; add at most one requested adapter | Engineering | Engineer completes the task unaided; errors and support time recorded |
| 5–10 Oct | Ask successful users to return with a second real task | Founder | 2 repeat uses on different tasks; flattering comments do not count |
| 8–12 Oct | Offer a tightly scoped paid next pilot to a team with a budget owner | Founder | Target 1 paid pilot or concrete budget/procurement commitment; distinguish either from revenue received |
| 12 Oct | Review demand and update application | Founder + engineering | Continue, narrow, pivot or stop based on the rules below |

Spend no money on APIs, new hardware, advertising or speculative compute during
this sprint. First use existing results and local analysis. If rerouting becomes
necessary, freeze a small experiment with the available quota before executing;
do not launch repeated large sweeps just to increase activity.

### Prospect selection

Prioritize engineering teams with a recent public FPGA accelerator or toolchain
project and evidence that someone owns architecture evaluation. Start with people
the founder can reach through existing technical communities. Separate independent
reviewers, noncommercial users and budget-owning teams in the tracker.

Do not spend the first week trying to sell to large semiconductor procurement
departments. Do not count competitors, paper authors or an email list as demand.
Record public source, role relevance and the proposed reason for contact before
any message is sent. No outreach has been sent by this sprint preparation.

### Interview script: 15 minutes

1. Tell me about the last time you compared FPGA accelerator architectures.
2. What files and tools did you use, and which part took the longest?
3. What went wrong or forced you to rerun work? Can you show a nonconfidential example?
4. How often does that happen, and what gets delayed when it does?
5. Who owns that decision and who could approve spending to improve it?
6. If relevant, ask to observe them doing one comparison with the preview.
7. Agree a concrete next task and date. Avoid asking only whether the idea sounds useful.

### Draft invitation: personalize before sending

> Hi [name], I’m building Kernellum and testing a small tool for comparing FPGA
> accelerator variants from existing route results. I noticed [specific relevant
> project]. Could I ask how you currently decide between architectures and where
> that process gets slow or unreliable? I have a working K1/ECP5 prototype, but
> I’m first trying to understand a real workflow. Would a 15-minute conversation
> this week be useful?

### Pilot record

Keep identifiable customer records private, outside this public repository.
For each pilot record: team ID; role; dated permission; workflow/problem;
baseline method; agreed input scope; source and tool versions; timing constraints;
manual task time; assisted task time; correctness review; support minutes;
decision changed; second task requested/completed; budget owner; payment status;
next action and date. Unknown fields remain unknown. Do not publish customer
names, RTL, screenshots, quotes or data without permission.

### Pilot success and stop rules

- Treat a workflow as promising when at least 3 of 10 qualified interviews
  independently describe the same frequent problem and at least 2 provide a
  real task. This is an internal directional threshold, not statistical proof.
- For time savings, agree the same task and correctness criteria before running
  either method. Include setup and support time. Do not substitute the 23.56%
  research latency result for time saved by an engineer.
- If nobody supplies a task, revise the customer/problem hypothesis before
  expanding the product. More features will not repair absent interest.
- If use requires continuous founder interpretation, fix onboarding or offer
  an explicit engineering service; do not label it self-serve software.
- If engineers use it but budget owners will not pay, investigate whether the
  value belongs in a broader existing workflow before choosing pricing.
- If 2 teams repeat and one has a credible paid next task, concentrate the
  following month there. Research remains focused on a bottleneck those tasks expose.

## Technical evidence ledger for application claims

| Statement | Evidence | Boundary |
| --- | --- | --- |
| K1 closed-loop study improved the routed-derived optimum on 12/12 workloads | `results/k1_closed_loop_validation.json`, K1 report | One frozen family, modeled cycles plus routed Fmax; not customer traction |
| Earlier portfolio study reported 23.56% mean workload latency improvement | `results/similarity_portfolio_summary.json`, portfolio report | 36 deployment cases share a study; no board measurement; 70.57% mean FF overhead |
| B-local achieved a robust new breakthrough | Rejected by final prospective and novelty audits | Do not claim it |
| Route Review runs on existing K1 data | Runnable command and example report | Engineering preview, retrospective ranking |
| Customers save time or money | No verified record in reviewed materials | Must be measured externally |
| Novel IP, superior commercial EDA or universal timing law | Not established | No claim |

## YC working draft

This is content preparation, not an application submission. Confirm the current
form, founder details and business facts before copying answers.

**Short description (43 characters):**

Tools for FPGA accelerator design decisions

**What are you building?**

Kernellum is developing tools that help accelerator engineers choose hardware
architectures using evidence from synthesis and routing. Our first working
prototype takes a GEMM workload, resource limits and existing K1 route results,
then produces a ranked comparison with explicit failure reasons and traceable
inputs. We are starting with a narrow FPGA implementation to test whether this
workflow helps engineers make real design decisions.

**How far along are you?**

We have a reproducible research codebase covering model-to-RTL experiments,
architecture search, functional simulation and routed evaluation, plus a runnable
route-comparison preview. An earlier bounded ECP5 study reported a 23.56% mean
modeled workload-latency improvement using routed timing, with increased register
cost. A later architectural hypothesis failed its prospective tests and is closed.
External product validation is the next milestone. [Insert only verified current
user counts, usage and revenue; do not use internal experiment counts as users.]

**What do you understand about this problem?**

Our experiments show that an attractive analytical architecture can change rank
after physical routing, and routing variability can change the preferred candidate.
This led us to focus on decisions that remain traceable to implementation evidence.
We still need to establish where this causes enough pain in a customer's existing
workflow to justify adopting another tool.

**How will you make money?**

The initial hypothesis is a scoped engineering pilot, followed by recurring team
software if users repeatedly need the workflow. Pricing and willingness to pay
are unvalidated. We will test them with the person who owns the engineering budget.

**Long-term ambition**

Kernellum's broader mission is to build systems that reason, investigate and
discover. Architecture engineering is our first concrete application: an environment
where hypotheses can be implemented and evaluated. Expansion follows demonstrated
technical transfer and customer use.

**Founder input still required**

Confirm company/legal status, current founders and equity, each person's actual
contributions, employment/study commitments, availability to work full-time,
verified users/revenue and the preferred batch. Founder achievements should use
specific verifiable work, with a clear account of what the founder personally
built and can explain. The founder must record the video and own these answers.

## Application timing and sources

As checked on 28 September 2026, YC's application page lists Winter 2027
(January–March in San Francisco), with an on-time deadline of **2 November 2026,
8 pm Pacific**, equivalent to **3 November, 9:30 am IST**. Verify before submitting.
YC states that idea-stage companies can apply and that founders must commit
full-time during the batch and afterwards. Its Early Decision option allows
students to request a later batch. Choose based on actual availability; do not
promise a school or relocation decision that has not been made.

There is no published universal 'YC-level' checklist or guaranteed acceptance
threshold. This sprint strengthens the evidence, but an application need not
wait for these traction targets or a scientific breakthrough.

Primary sources checked 28 September 2026:

- [YC FAQ](https://www.ycombinator.com/faq)
- [Apply to YC](https://www.ycombinator.com/apply)
- [Early Decision](https://www.ycombinator.com/early-decision)
- [How to Apply](https://www.ycombinator.com/howtoapply)
- [Silimate](https://www.ycombinator.com/companies/silimate)
- [Silogy](https://www.ycombinator.com/companies/silogy)
- [ChipAgents](https://chipagents.ai/)
- [SiliconCompiler documentation](https://docs.siliconcompiler.com/en/latest/)

Repository audit baseline: `f71c0fa83622c889446e205c60ec9c84ec3bb8e6`.
Research conclusions are based on the cited committed records; this sprint
does not claim to have independently rerun their physical-design experiments.
