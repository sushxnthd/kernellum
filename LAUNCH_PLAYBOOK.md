# Kernellum Technical Launch Playbook

## Objective

The launch should create **technical curiosity and third-party inspection**, not look like a fundraising announcement.

The desired loop is:

```text
technical artifact
      ↓
engineers inspect / reproduce
      ↓
credible public discussion
      ↓
design-partner interest
      ↓
external benchmark evidence
      ↓
investor attention
```

## Canonical positioning

**Kernellum is building an AI-native compiler for workload-specific accelerators.**

A supported neural workload and deployment constraints are lowered to hardware IR, searched across candidate architectures, emitted as inspectable SystemVerilog and accompanied by verification evidence.

Current status: research-stage prototype. Physical FPGA evidence is the next threshold.

## Launch order

### 1. GitHub / site
Already canonical. Every post should resolve to the repository or evidence explorer rather than to a vague landing page.

### 2. Show HN

Suggested title:

> Show HN: Kernellum – a model-to-RTL compiler for small AI accelerators

Suggested body:

> I’ve been building Kernellum, a research-stage model-to-hardware compiler.
>
> The current prototype takes a deliberately narrow neural workload through INT8 lowering, hardware IR, constraint-driven architecture search, generated SystemVerilog, cycle-level verification, RTL simulation and ECP5-family synthesis.
>
> For the current digits MLP: 96.44% INT8 held-out accuracy, 450/450 cycle-model agreement, 32/32 RTL golden-vector cases, and Yosys/ECP5 family synthesis. I’m explicitly not claiming the modeled 6.8 µs as physical latency—the next milestone is a named ECP5 board, P&R, timing closure and measured power/latency.
>
> I’m particularly interested in criticism from compiler / FPGA / EDA people: what evidence would you require before taking an automated model-to-accelerator flow seriously?
>
> Repo: https://github.com/sushxnthd/kernellum
> Evidence: https://sushxnthd.github.io/kernellum/evidence.html

### 3. LinkedIn

> I’m building **Kernellum**, an AI-native model-to-hardware compiler.
>
> Instead of treating hardware as a fixed deployment target, the compiler takes the workload and deployment constraints into the design loop: model → hardware IR → architecture search → generated RTL → verification.
>
> The first public compiler slice is intentionally narrow, but reproducible: 96.44% INT8 held-out accuracy, 450/450 exact cycle-model agreement, 32/32 RTL golden-vector simulations, and ECP5-family synthesis.
>
> The next threshold is physical: named FPGA, place-and-route, achieved Fmax, measured latency and energy/inference.
>
> I’m opening a small design-partner program for compact, non-confidential inference workloads. I’d rather test the system on a real constraint than add another toy demo.
>
> https://sushxnthd.github.io/kernellum/
> https://github.com/sushxnthd/kernellum

### 4. X / technical thread

Post 1:
> Building Kernellum: an AI-native compiler that maps neural workloads + deployment constraints into accelerator architectures, RTL and verification evidence.

Post 2:
> Current public slice: INT8 lowering → hardware IR → architecture search → SystemVerilog → cycle verification → RTL sim → ECP5-family synthesis.

Post 3:
> Current evidence: 96.44% INT8 accuracy, 450/450 cycle agreement, 32/32 RTL golden vectors. Physical P&R / latency / power are still unclaimed.

Post 4:
> The next milestone is the one that matters: make the generated accelerator run on a named FPGA and publish Fmax, utilization, latency and energy/inference.

Post 5:
> I’m looking for compact, non-confidential workloads to test as design-partner evaluations.
> https://github.com/sushxnthd/kernellum

## Community distribution

Use technical communities only when the post has a genuine discussion prompt.

Potential surfaces:
- Hacker News / Show HN
- FPGA and hardware-design communities
- compiler / ML-systems communities
- LinkedIn semiconductor / EDA network
- X hardware / systems researchers
- relevant university labs and open-source hardware communities

Do not cross-post identical promotional copy everywhere. Lead with the engineering question relevant to each community.

## Investor-facing rule

Do not lead with “raising” until the evidence and external-use signals are stronger.

Lead with:
1. what the system does;
2. what is already reproducible;
3. what physical evidence is next;
4. who is evaluating it externally.

Inbound investors should discover a technical project that looks like it is becoming a company—not a company page searching for a technical project.

## What to measure after launch

Track:
- GitHub stars / forks;
- unique technical contributors;
- serious issues or pull requests;
- design-partner inquiries;
- external reproduction attempts;
- invitations to demos / events / podcasts;
- inbound from semiconductor engineers;
- inbound from investors.

The strongest signal is not raw traffic. It is an external team giving Kernellum a real workload or an experienced hardware engineer choosing to engage with the technical work.
