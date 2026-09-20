# Project SIMILARITY: timing-metric audit result

Date: 2026-09-20

## Finding

The historical SIMILARITY timing parser did **not** mix primary-clock and cross-domain frequencies. All four audited routes contained no cross-domain Fmax values, and the historical minimum always belonged to the primary clock.

However, the parser did mix **implementation stages**.

nextpnr performs timing analysis after placement and again after routing. The historical regex collected every primary-clock "Max frequency" line and retained the minimum, which usually selected the post-placement estimate rather than the final post-route timing.

Source-code inspection confirms the execution order:

1. the placer calls `timing_analysis(ctx)`, printing Fmax;
2. the router completes;
3. router1 calls `timing_analysis(... print_fmax=true, print_path=true, update_results=true)`, producing the final routed timing result;
4. `--report` writes the updated post-route timing result.

## Audit routes

ECP5-85K, seed 16:

| Topology | N | First/placement Fmax | Final/routed Fmax | Historical parser selected |
| --- | ---: | ---: | ---: | --- |
| broadcast | 5 | 77.12 MHz | 92.55 MHz | 77.12 MHz |
| broadcast | 9 | 63.10 MHz | 83.04 MHz | 63.10 MHz |
| local | 5 | 100.33 MHz | 105.42 MHz | 100.33 MHz |
| local | 9 | 88.30 MHz | 100.77 MHz | 88.30 MHz |

Thus the historical metric is a reproducible **worst implementation-stage Fmax**, but it must not be called the final routed critical period.

## Immediate consequence

The earlier causal direction survives these audit points using final routed timing:

N=5:
- routed broadcast period ~= 10.805 ns
- routed local period ~= 9.486 ns
- routed broadcast tax ~= 1.319 ns

N=9:
- routed broadcast period ~= 12.042 ns
- routed local period ~= 9.924 ns
- routed broadcast tax ~= 2.118 ns

But all previously reported numerical equations and slope magnitudes were derived from the historical worst-stage metric and therefore **must not be promoted as routed-timing laws**.

## Required correction

All final SIMILARITY timing claims must henceforth use nextpnr `--report` and read the post-route `fmax` object directly.

The causal topology experiment and its independent confirmation must be rerun under this corrected measurement definition before any final discovery claim is made.
