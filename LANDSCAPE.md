# Kernellum — Technical Landscape

Kernellum operates at the intersection of ML compilation, accelerator architecture search and electronic design automation. The category is active; the thesis is **not** that alternatives do not exist.

The intended differentiation is the interface:

```text
trained ML workload + deployment constraints
                  ↓
         architecture search
                  ↓
      workload-specific hardware
                  ↓
       generated RTL + evidence
                  ↓
   physical feedback into the backend
```

## Adjacent approaches

| Approach | Typical starting point | Typical output / role | Relationship to Kernellum |
|---|---|---|---|
| High-level synthesis (for example AMD Vitis HLS) | C/C++ hardware-oriented function | RTL / FPGA IP | HLS automates implementation of an algorithm already expressed for hardware. Kernellum is exploring a higher-level starting point: the ML workload plus deployment constraints. |
| ML compiler stacks (for example Apache TVM / TIRx) | tensor programs / ML kernels | optimized code for GPUs and specialized accelerator backends | ML compilers primarily optimize software/kernel execution for a target. Kernellum is exploring generation and selection of the target accelerator microarchitecture itself. |
| Agentic EDA (for example Agentrys) | semiconductor design workflows, tools and organizational methodology | agents operating verification / physical-design and other chip-design workflows | Closely adjacent in AI-for-chip-design, but oriented around automating existing design workflows. Kernellum's current wedge is workload-to-accelerator compilation. |
| AI-first chip design platforms (for example Cognichip ACI) | system / chip-design problems | broad architecture, PPA and chip-design assistance | Demonstrates that AI-native semiconductor design is a serious category. Kernellum is currently much narrower: reproducible ML accelerator generation with an explicit compiler/evidence chain. |

## Why the wedge may matter

### 1. The workload is part of the hardware specification

Kernellum does not begin from hand-written C/C++ hardware code or an already-chosen accelerator target. Model structure, numeric precision and deployment constraints are intended to influence the architecture.

### 2. Architecture search is explicit

Candidate architectures are represented and compared rather than hidden behind a single generated answer. The present search space is small; the long-term opportunity is to make it increasingly physical-design aware.

### 3. The output is inspectable

Generated RTL, weights, golden vectors, cycle-level reference behavior and EDA logs are intended to make the result auditable.

### 4. Physical feedback is part of the roadmap

The first ULX3S-85F reference P&R attempt exposed a timing bottleneck in the generated datapath. The backend is being restructured in response. That feedback loop — model -> architecture -> RTL -> physical result -> compiler improvement — is central to the thesis.

## Current boundary

Kernellum is not currently a replacement for mature commercial EDA or HLS suites.

The public compiler is still narrow:
- sequential dense neural networks;
- signed INT8 weights / activations;
- small FPGA-oriented accelerator configurations;
- open-source simulation / synthesis / P&R evidence.

The next proof points are timing-closed reference P&R, physical-board measurement, broader operator/model coverage and external design-partner workloads.

## Primary references

- AMD Vitis HLS: https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vitis/vitis-hls.html
- Apache TVM / TIRx: https://tvm.apache.org/docs/tirx/overview.html
- Agentrys: https://agentrys.ai/
- Cognichip: https://www.cognichip.ai/

This document describes positioning, not a claim that the listed systems are technically equivalent.
