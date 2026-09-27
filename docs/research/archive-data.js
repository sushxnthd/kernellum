window.KernellumResearchArchive = {
  reports: [
    {
      id: "KRN / TR-002",
      shortId: "TR-002",
      slug: "tr-002",
      date: "2026-09-21",
      dateLabel: "21 September 2026",
      type: "Technical report",
      topic: "Causal timing law / route-robust selection",
      title: "Project SIMILARITY: Learning Routed Timing Laws for Architecture Search",
      summary: "A causal topology intervention isolates operand-distribution topology as an architecture variable, freezes a routed timing law, and tests a bounded two-candidate selection policy on unseen deployment routes.",
      metrics: ["96 / 96 causal routes", "0.3039 ns held-out MAE", "36 / 36 unseen deployment wins", "23.56% mean latency improvement"],
      featured: true,
      href: "/kernellum/research/tr-002/",
      source: "https://github.com/sushxnthd/kernellum/blob/main/docs/SIMILARITY_ROUTED_LAW_REPORT.md"
    },
    {
      id: "KRN / TR-003",
      shortId: "TR-003",
      slug: "tr-003",
      date: "2026-09-20",
      dateLabel: "20 September 2026",
      type: "Technical report",
      topic: "Closed-loop architecture search",
      title: "Closed-Loop Physical-Design Search",
      summary: "Final-route observations are folded back into architecture selection under a fixed implementation budget, comparing active acquisition against an equal-budget random control.",
      metrics: ["17 / 172 designs attempted", "8 / 8 new routes successful", "6.475% Fmax MAPE", "12 / 12 workloads improved"],
      featured: true,
      href: "/kernellum/research/tr-003/",
      source: "https://github.com/sushxnthd/kernellum/blob/main/docs/K1_CLOSED_LOOP_REPORT.md"
    },
    {
      id: "KRN / TR-001",
      shortId: "TR-001",
      slug: "tr-001",
      date: "2026-09-17",
      dateLabel: "17 September 2026",
      type: "Technical report",
      topic: "System / compiler / physical evidence",
      title: "Kernellum Compiler and Physical-Evidence Pipeline",
      summary: "A system-level record connecting quantized model-to-RTL generation, analytical search, synthesis calibration, final-route measurement, closed-loop physical feedback, and the K2 board-validation handoff.",
      metrics: ["96.44% INT8 held-out accuracy", "450 / 450 cycle-model exact matches", "0.9441 K1 rank Spearman", "12 / 12 active-search improvements"],
      featured: false,
      href: "/kernellum/research/tr-001/",
      source: "https://github.com/sushxnthd/kernellum/blob/main/docs/EXPERIMENT_LEDGER.md"
    }
  ],
  evidence: {
    id: "KRN / EVD-001",
    shortId: "EVD-001",
    date: "2026-09-21",
    dateLabel: "21 September 2026",
    type: "Evidence dossier",
    topic: "Evidence control / publication bundle",
    title: "Kernellum Evidence Dossier",
    summary: "A claim-to-artifact record connecting the compiler, K1 routed search, Project SIMILARITY, machine-readable results, and the K2 validation handoff into one diligence path.",
    metrics: ["Claim-to-artifact traceability", "Machine-readable evidence map", "Research review path", "K2 handoff record"],
    href: "/kernellum/research/evidence/",
    source: "https://github.com/sushxnthd/kernellum/blob/main/docs/EXPERIMENT_LEDGER.md"
  }
};