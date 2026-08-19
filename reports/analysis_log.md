# Analysis Log — Marketing A/B Test

Companion to the README and report. The report states what was found and
recommended; this document records how each decision was reached, including the
ones that were reversed.

## Decision log

| Decision | Reasoning |
|---|---|
| One-sided primary test | The business decision is directional: act only if ads outperform PSA. A two-sided chi-square is reported as a cross-check so the result does not depend on test choice. |
| Interval reported instead of point estimate | Exactly one ROI scenario changes sign across the lift interval, so the interval is decision-relevant rather than decorative. |
| Cramer's V reported alongside chi-square | At n = 588,101 almost any difference reaches significance. V distinguishes detectable from large. |
| PSA chosen as standardization reference | The counterfactual implied by the business question is what the ad group would have converted at with PSA-like timing. The reverse direction is reported for symmetry. |
| Breakeven as primary cost output | Requires one assumption rather than two, and hands the remaining judgement to whoever knows their conversion value. |
| No daypart ROI | ROI is inherently a causal claim. Running money through a segmentation already declared descriptive would reintroduce the attribution problem that section fenced off. |
| No reallocation recommendation | The timing pattern sits on a fork whose two branches imply opposite actions. A monitored reallocation would silently assume one of them. |

## Corrections made during analysis

**Hand-estimated chi-square values were replaced by formal tests.** Initial
by-hand estimates (~246 for day, ~200 for hour) were close but were replaced with
formal `chi2_contingency` results: 235.61 (day, dof 6, p = 4.849e-48) and 192.29
(hour, dof 23, p = 1.095e-28).

**Prediction that timing spread would be small was wrong.** Day spread (1.19 pp)
and hour spread (2.33 pp) within the ad group both turned out to exceed the
topline lift (0.7692 pp) — the opposite of what was expected going in.

**Initial power estimate was off by roughly 2x.** An early estimate of ~8,500
users per arm for a 0.50 pp MDE was corrected to the actual formal calculation:
17,083 per arm (34,167 total, power 0.80, alpha 0.05, two-sided).

**Standardized CI initially assumed the reference weights were fixed.** The
analytic SE for the standardized lift summed weighted cell-level binomial
variance plus the PSA rate variance, which conditions on the PSA day x hour
weights as known. They are estimated from 23,524 users over 168 cells. A
10,000-replicate bootstrap that resamples the weights gives [0.5991, 0.9495] pp
against the analytic [0.6023, 0.9510] pp. The analytic interval was kept as
primary — the gap is 0.003 pp at the lower bound and changes no ROI cell's sign —
and the assumption is now stated rather than left implicit.

**Thin-cell flag was insufficient for segment ranking.** The `thin` flag was
defined against PSA reference weight during the standardization diagnostics, then
reused for ad-group segment ranking. It does not transfer: Saturday 06:00
(n = 252, 13 conversions, 5.16%) passed unflagged. The operative guardrail for
segment rankings is the n >= 500 filter, and the report states this rather than
implying the flag was sufficient.

**Leave-one-out diagnostic initially conflated two effects.** The all-cell test
produced a maximum swing of 0.02454 pp, larger than the standardization change of
0.0074 pp, which would have undercut the finding if reported without
qualification. The five largest swings came from high-volume mainstream cells, not
thin cells, indicating a weight effect rather than noise. Restricting the test to
thin cells (max swing 0.00279 pp) and benchmarking against removal of the 28
highest-weight cells (a 4.2x larger shift) separated the two.

## Expected objections, and where they are answered

| Objection | Answer |
|---|---|
| "The groups differ on timing, doesn't that explain the lift?" | Direct standardization moves the lift by +0.0074 pp, in the direction favouring ads. Both reference directions agree. |
| "The PSA group is only 4% of the sample, is it stable?" | CI width 0.338 pp against a 0.769 pp gap. Stable enough for this comparison, though far less precise. |
| "p = 4.85e-48 on day looks alarming." | Cramer's V is 0.0200. The association is negligible in magnitude and detectable only because of sample size. |
| "Missing PSA rows in some hours?" | Zero hours lack PSA rows. Share ratio ranges 0.744 to 1.145 with no value near zero. |
| "Does the standardized CI account for uncertainty in the reference weights?" | No — the analytic SE treats them as fixed. The bootstrap that resamples them is reported alongside: [0.5991, 0.9495] pp against [0.6023, 0.9510] pp. |
| "43% relative lift seems too large." | Stated as a reason for scepticism rather than celebration, and the reason the cost scenario was run at all. |
| "Best-performing slot is 5.68%, why not target it?" | That cell holds 5 conversions from 88 impressions. Rankings are filtered to n >= 500. |

## What this dataset could not answer

- Whether assignment was genuinely random, for lack of pre-treatment covariates
- Whether the campaign was profitable, for lack of cost and revenue data
- Whether daypart timing causes conversion or merely correlates with user type
- Whether 24.82 impressions per user reflects an efficient frequency cap

Each of these is a data collection requirement, not an analysis failure. The
proposed daypart experiment in the report is specified to close the third and
would generate the logging needed for the first.
