# Project SIMILARITY: arithmetic-backend replication

Date: 2026-09-20

## Result

The preregistered arithmetic-backend replication gate **FAILED**.

All **54/54 routes succeeded**. DSP-backed designs mapped exactly one MULT18X18D per PE and LUT-forced designs mapped zero DSPs, so the backend intervention itself worked as intended.

The square-root model fitted only on 45K transferred to held-out 25K and 85K on both backends:

| Backend | 25K sqrt MAPE | 85K sqrt MAPE | Combined sqrt MAPE | Combined linear-PE MAPE |
| --- | ---: | ---: | ---: | ---: |
| DSP | 2.92% | 5.09% | **4.36%** | 6.11% |
| LUT | 5.03% | 4.29% | **4.54%** | 5.46% |

Thus the frozen square-root model beat the frozen linear-PE model on the combined held-out data for both arithmetic backends.

However, the preregistered stability criterion failed:

- DSP median seed CV: **2.63%**
- LUT median seed CV: **7.40%**
- frozen threshold: <= 6% for each backend

Therefore the full replication gate fails.

## Important diagnostic

After the gate was evaluated, the exploratory exponent scan selected:

- DSP: p = **0.29**
- LUT: p = **0.28**

These exponents are similar across backends but are not close to 0.5.

This is evidence against treating sqrt(PE) as a universal exponent. The previously confirmed square-root equation remains a strong predictive law for its original RTL family, but the simplified matched fabrics suggest that the deeper invariant may involve broadcast/routing structure rather than PE count alone.

## Scientific consequence

Supported:

> A compact array-size model transfers across DSP-backed and LUT-forced implementations with approximately 4.4-4.5% held-out error, and square-root outperforms a linear-PE baseline in this protocol.

Not supported:

> The square-root exponent is universal across arithmetic backends.

The next experiments should explicitly separate broadcast fanout, number of simultaneous broadcasts, sink density, and routing congestion rather than fitting PE count alone.
