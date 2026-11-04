---
name: null-calibration
description: >-
  Calibrates a "changed / stable / trend" selection rule on a placebo or shuffled null before it is applied to a small sample, and presents each candidate threshold with its measured false-positive rate and resulting counts when the user is asked to choose. Use this whenever features, channels, or metrics are being screened with a threshold on few subjects, sessions, or days — a pilot, n = 1–10, before/after or condition A/B comparisons, "≥ k× noise", "same sign in every pair", "slope above X" — and whenever the user is about to be asked to pick such a threshold: "篩選特徵", "哪些特徵有反應", "哪些指標有變化", "哪些是穩定的", "閾值怎麼設", "門檻要多少", "有沒有趨勢", "responder", "screening", "feature selection".
---

# Calibrating a selection rule on a null

On a small sample, a threshold that sounds strict can pass a large share of features by chance. Two subjects, rule approved in the abstract ("changed" = ≥ 2× re-wear noise with every pair the same sign; "stable" = ≤ 1× noise): more than half of the features came out as meal-responsive and almost none as stable. Relabelling same-type days as a placebo then passed 38 % of features as "changed", and a time shuffle passed 22–36 %. The rule was measuring noise, and nothing in the abstract wording revealed that.

## Procedure

1. **Write the rule as a function of the labelled data** — `passing = rule(data, threshold)` returning the set of features that pass — so it can be rerun unchanged on relabelled copies. → verify: on the real labels it reproduces the counts already reported.
2. **Build nulls in which no effect exists by construction.** Use both kinds when the design allows:

   - *Placebo*: compare units of the same type as if they were different conditions (two ordinary days labelled "before" and "after", two re-wears labelled A and B).
   - *Shuffle*: permute condition labels or time order within each subject; use block shuffles when samples are autocorrelated.

   With a small sample, enumerate every distinct relabelling instead of drawing random ones, and say how many there are; with fewer than about 5, report that the null is coarse.

3. **Measure the rule on every null.** For a "changed" or "trend" rule, the pass rate on the null is its false-positive rate. For a "stable" rule, the placebo pass rate is how often a truly stable feature is recognised as stable, so a low value means the rule is too strict. Report the mean and the range across relabellings.
4. **Sweep the candidate thresholds**, including the one already proposed, and fill the table below. Compare each real-data count with the count expected from noise alone: null pass rate × number of features.
5. **Ask the user with the table, never with the abstract rule.** If no threshold puts the real count clearly above the noise-only count, say plainly that this sample cannot separate signal from noise with this rule, rather than offering a threshold to pick.

## Output format

```markdown
Rule: <exact rule>   Features: <N>   Sample: <subjects / sessions / days>
Nulls: placebo = <how built, k relabellings>; shuffle = <how built, k relabellings>

| Threshold | Placebo pass rate | Shuffle pass rate | Expected by noise (count) | Real data (count) |
| --- | --- | --- | --- | --- |
| <t1> | <mean % (min–max)> | <mean % (min–max)> | <rate × N> | <n> |
| <t2> | ... | ... | ... | ... |

Recommendation: <threshold, or "this sample cannot separate signal from noise with this rule">
```

## Verification

1. Every threshold offered to the user has a null pass rate measured on this data, not one assumed from elsewhere.
2. The table reports the number of relabellings behind each rate.
3. The threshold finally applied is one the user chose from the table, and the report states its expected-by-noise count next to the selected count.
