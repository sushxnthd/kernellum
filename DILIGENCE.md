# Kernellum — Public Diligence Index

This page is the shortest route through Kernellum's public evidence.

## 1. Thesis

- [Investor brief](INVESTOR_BRIEF.md) — product wedge, evidence, milestones and commercial direction.
- [Technical landscape](LANDSCAPE.md) — how Kernellum is positioned relative to HLS, ML compilers and AI-for-EDA.
- [Roadmap](ROADMAP.md) — staged technical development.
- [Technical diligence FAQ](FAQ.md) — direct answers to common technical and venture questions.

## 2. Technical evidence

- [Evidence explorer](https://sushxnthd.github.io/kernellum/evidence.html) — headline claims mapped to artifacts.
- [TR-001](https://sushxnthd.github.io/kernellum/TR-001.pdf) — first technical report.
- [Benchmark policy](BENCHMARKS.md) — evidence ladder from model quality to physical measurement.
- [Build status](BUILD_STATUS.md) — current synthesis / FPGA status.
- [KRN-PNR-001](research/ULX3S_PNR_SWEEP_2026-09-18.md) — ULX3S-85F 1/2/4/8-lane P&R sweep, timing feedback and selected reference configuration.
- [KRN-HW-001 protocol](research/KRN-HW-001_PROTOCOL.md) — frozen physical-board programming, latency, power and energy measurement method; measurements still pending.
- [Repository](https://github.com/sushxnthd/kernellum) — source, tests and reproducibility.

## 3. Product surface

- [Compiler](https://sushxnthd.github.io/kernellum/compiler.html)
- [Research](https://sushxnthd.github.io/kernellum/research.html)
- [Hardware tracker](https://sushxnthd.github.io/kernellum/hardware.html)
- [Research log](https://sushxnthd.github.io/kernellum/log.html)

## 4. External validation

- [Design Partner Program](DESIGN_PARTNERS.md)
- [Open benchmark call](https://github.com/sushxnthd/kernellum/issues/2)
- [KRN-EXT-001 result](research/KRN-EXT-001_RESULT.md) — completed clean-room third-party public-model evaluation: 64→64→64→32, 2 lanes selected at 28.18 MHz on the 25 MHz ULX3S target.
- [KRN-EXT-001 protocol](research/KRN-EXT-001_PROTOCOL.md) — frozen provenance, selection and evidence rules.

KRN-EXT-001 is completed external public-model evidence. External customer/design-partner validation remains a separate commercial milestone.

## 5. Physical validation

- [KRN-HW-001 tracker](https://github.com/sushxnthd/kernellum/issues/1) — physical ULX3S execution and measurement.
- [ULX3S hardware-access call](https://github.com/sushxnthd/kernellum/issues/9) — request for compatible board access or a reproducible third-party measurement run.

The programming/capture/analyzer tooling is ready; no physical-board latency, power or energy result is promoted until raw measurement evidence exists.

## 6. Current evidence boundary

The project distinguishes:
- model / quantization accuracy;
- cycle/reference-model agreement;
- RTL simulation;
- family-level synthesis;
- board-targeted place-and-route;
- physical-board measurement.

A result is not promoted to the next evidence level until the corresponding artifact exists.

## 7. Founder

**Sushanth Dasari — Founder & Research Lead**

- GitHub: https://github.com/sushxnthd
- Kernellum: https://sushxnthd.github.io/kernellum/

---

For partnership or early deep-tech conversations: https://sushxnthd.github.io/kernellum/partner.html
