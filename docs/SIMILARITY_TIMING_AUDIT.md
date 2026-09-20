# Project SIMILARITY: timing-metric audit

Date: 2026-09-20

## Purpose

Most SIMILARITY routing scripts historically parse nextpnr timing with:

    Max frequency[^:]*: <value> MHz

and retain the minimum matched value.

nextpnr can emit both:

- per-clock-domain "Max frequency for clock ..." lines;
- related cross-domain "Max frequency for A -> B ..." lines.

Before treating the accumulated timing laws as final, audit exactly which line class limits the recorded metric and whether the same metric class is being compared across topologies and sizes.

This is a measurement audit, not a hypothesis test.

## Routes

ECP5-85K, seed 16:

- broadcast 5x5
- broadcast 9x9
- local 5x5
- local 9x9

For each route record:

- all per-clock Fmax lines;
- all cross-domain Fmax lines;
- minimum per-clock Fmax;
- minimum cross-domain Fmax;
- historical parser Fmax;
- whether the historical limiting value is a primary clock or cross-domain value.

If historical and primary-clock metrics differ, subsequent SIMILARITY claims must explicitly separate them and previously merged results must not be silently relabeled.
