---
name: stock-score-review
description: >-
  Turns scores the local pipelines already wrote into a ranked review across a covered universe — latest value, five-day weighted value, and the change that makes a name worth a second look — and layers the value / growth / quality / short and estimate-revision screens on top once fundamentals and earnings data are in the store. Use whenever the question spans more than one symbol: "今天哪幾檔有變化", "掃一遍名單", "幫我看評分變化", "這批分數怎麼樣", "哪幾檔值得看", "排一下名次", "篩一輪", "score review", "screen the watchlist", or after a scheduled run when the question is what moved. A single-symbol write-up belongs to `stock-research-note` — this skill ranks, it does not write notes.
---

# Reviewing scores across a universe

Adapted from the institutional idea-generation screen: filter a universe, hand back a shortlist, keep the shortlist labelled as candidates. The difference here is that the filter runs over **scores a scheduled run already computed**, not over a live market feed — and, as fundamentals and earnings data get added to these projects, over those too. Sections 4 and 5 are written for that data and activate the moment it exists in the store; until then they are the specification for what to build toward.

The interpreter path, `STOCKDATA_ROOT` and the silent `conda activate` failure are in each project's own CLAUDE.md (環境). One trap is worth restating because every review prints a table: this console is cp950, so keep emoji out of script output and set `PYTHONIOENCODING=utf-8` on anything printing Chinese.

## 1. Where the numbers are

Scores, today:

| Project | Store | What to read |
| --- | --- | --- |
| market-barometer | `%STOCKDATA_ROOT%\market.db` | `score_history` where `scope` in `index`, `macro_world`, `macro_tw` |
| stock-research | the same `market.db` (shared data layer) | `score_history` where `scope = 'stock'` |
| stock-rating | `<app dir>\.stock_rating\market.db` | `summary_history(code, market, as_of, payload)` — payload is JSON |
| stock-tracker | `<app dir>\.stock_tracker\data\ranking.db` | `LatestRanking(Rank, Symbol, Score, Suggestion, RecentScores)` |

Fundamentals and earnings, when they arrive: follow the storage pattern already in `schema.sql` — a flat table keyed by `(symbol, period)` with the payload as JSON, no JOIN, no ORM. Expect `fundamental_quarterly`, `estimate_snapshot` and `earnings_event` to be the three shapes worth separating, because they have different update cadences: statements change quarterly, estimates change weekly, events are dated.

Check what exists before assuming. `SELECT name FROM sqlite_master WHERE type='table'` costs nothing and decides whether sections 4 and 5 run at all.

## 2. Build the ranking

Three numbers per symbol, in this order:

| Number | Source | Why |
| --- | --- | --- |
| Latest | newest `as_of` for that symbol | where it stands |
| Five-day weighted | weights 10/15/20/25/30, `barometer.domain.weighting` | the smoothed read; one day is one observation |
| Δ | latest minus the previous `as_of` | what changed, which is usually the answer to the question being asked |

Sort by |Δ| descending. A name parked at 80 for six months is not news; a 30-point move overnight is, in either direction. Print the previous value next to the delta so the move can be read without a second query.

Compare each symbol against **its own** previous `as_of` rather than a shared date, and print that date on every row — the covered names span two session calendars and the newest row is not the same day for all of them.

## 3. Score screens

Run these over the scores themselves; they need nothing but what is already stored.

| Screen | Condition |
| --- | --- |
| Momentum turn | Δ ≥ +15 with the five-day weighted still below the latest — the move is new, not already averaged in |
| Breakdown | Δ ≤ −15, or the long-term dimension flipping from pass to fail |
| Divergence | short-term and long-term dimensions pointing opposite ways — the most interesting rows on the list |
| Quiet leaders | latest in the top quartile with |Δ| < 5 for five sessions — stable, worth a note rather than an alert |
| Flow-led | chips dimension moved while the price dimensions did not |

## 4. Fundamental screens — once fundamentals are stored

Straight from the source skill, with the thresholds kept as written. These are starting values for a small covered universe, not tuned parameters:

**Value** — P/E below sector median; EV/EBITDA below its own historical average; FCF yield > 5%; P/B < 1.5; dividend yield above market average.

**Growth** — revenue growth > 15% YoY; earnings growth > 20% YoY; growth rate accelerating quarter over quarter; margins expanding; ROIC > 15%.

**Quality** — five or more years of consistent revenue growth; stable or expanding margins; ROE > 15%; low debt/equity; high FCF conversion.

**Deterioration** — revenue declining or growth decelerating; margin compression; receivables or inventory rising faster than sales; valuation premium to peers with nothing explaining it; auditor changes or restatements.

**Special situation** — recent listing with a lockup expiry ahead; spin-off within twelve months; emerging from restructuring; management change at an underperformer.

For a Taiwanese name, monthly revenue (月營收) is the highest-frequency fundamental available and lands well before the quarterly statement — a growth or deterioration screen that ignores it is running a quarter behind.

## 5. Earnings screens — once earnings data is stored

| Screen | Condition |
| --- | --- |
| Reporting soon | next reporting date within the window; flag so a score move is not read as fundamental news when it is positioning |
| Beat/miss history | last four quarters against estimate — a name that beats consistently and one that misses consistently deserve different readings of the same score |
| Estimate revision | forward estimate revised up or down since the previous snapshot; direction matters more than level |
| Post-report drift | score change in the sessions following a report, against the beat/miss sign |
| Guidance change | current guidance versus prior, where guidance is published |

Reporting cadence differs across the covered universe, and a screen with one hard-coded calendar will silently miss half the list:

| | US | TW |
| --- | --- | --- |
| Quarterly filing | 10-Q, 10-K annually, on EDGAR | 季報 via MOPS; statutory deadlines about 5/15, 8/14, 11/14, annual 3/31 |
| Monthly | — | 月營收, published by the 10th of the following month |
| Call | earnings call with transcript | 法說會, not every company, not every quarter |

## 6. Output format

```markdown
## 有變化的（依 |Δ| 排序）

| 標的 | as_of | 最新分 | 五日加權 | Δ vs 前一交易日 | 主要變動維度 | 命中的篩選 |
|---|---|---|---|---|---|---|

## 基本面／財報命中（資料存在時才有這一節）

| 標的 | 篩選 | 關鍵數字 | 期別 | 下次公布 |
|---|---|---|---|---|

## 沒有變化的

（只列代號）

> 篩選出來的是候選，不是結論 —— 每一列都還需要自己看過。
```

The footer carries the one idea worth keeping from the source skill: a screen surfaces candidates and nothing more. The best rows are usually intersections — a quality name at a value price because of a temporary headwind — and an intersection is still a candidate.

## 7. Verification

A review is not done until these have been checked (global: Goal-Driven Execution):

1. The `as_of` printed on each row is the one actually stored, and no header claims a single date for the whole table.
2. Every Δ has its previous value shown next to it.
3. Sections 4 and 5 either ran against tables confirmed to exist, or are absent — not filled with placeholders.
4. Screen hits name the condition that fired, not just the screen's name.
5. The candidates-not-conclusions footer is present.
