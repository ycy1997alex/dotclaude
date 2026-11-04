---
name: stock-research-note
description: >-
  Writes a zh-TW research note on one named stock out of data the local pipeline produced — chaining the price series, the three-term scores, the chips dimension and the macro backdrop into a fixed template where every number names its source, its `as_of` and the run that wrote it — and expands into a full update with fundamentals, valuation and beat/miss analysis once that data is in the store. Use when one symbol is asked about by name: "幫我看 2330", "寫一份 TSM 的研究筆記", "這檔現在什麼狀況", "做一份筆記", "財報出來了幫我更新", "research note for NVDA". Ranking several names at once belongs to `stock-score-review`.
---

# Writing a single-name research note

Adapted from two institutional skills: a tool-chaining research snapshot (consensus, fundamentals, prices, macro, then synthesise) and an earnings update (fixed length, lead with what is new, cite every figure to a filing). What transfers is their structure and their citation discipline, pointed at local data:

| Their rule | Here |
| --- | --- |
| Chain the data tools, then synthesise | Chain price series → three-term score → chips → macro backdrop → fundamentals when present |
| Cite every figure to a filing with a link | Every number names its file or table, its `as_of`, and the run that wrote it |
| Lead with what is new since last quarter | Lead with what changed since the previous session, or since the last report when there is one |
| Conclude with a recommendation | Conclude with a rule-derived action description that names the rule it came from |

The interpreter path, `STOCKDATA_ROOT`, `PYTHONPATH` for both `src` trees and the silent `conda activate` failure are in the project's own CLAUDE.md (環境與指令). Set `PYTHONIOENCODING=utf-8` and keep emoji out of output — this console is cp950 and the note is full of Chinese.

## 1. Two sizes

| Mode | When | Length |
| --- | --- | --- |
| Score note | routine; price and score data only | one page |
| Full update | a report has landed, or fundamentals are in the store | three to four pages, sections 4 and 5 included |

Pick by what the data supports, not by how much there is to say. A one-page note on a quiet name is the correct output, and padding it to look thorough is how a note stops being read.

## 2. Inputs to chain

| Step | Source | Notes |
| --- | --- | --- |
| Price series | `csv_audit.read_current(symbol)` → `%STOCKDATA_ROOT%\price_current\` | bars carry `close` and `volume_shares`; shares internally, 張 only at display |
| Three-term score | `market.db` `score_history` where `scope='stock'`, or recompute via `research.domain.scoring_stock.score_stock` | `subscores_json` holds short / mid / long / chips |
| Five-day weighted | `research.pipeline.run_stock_scores.summarize_window` | weights 10/15/20/25/30, shared across the macro, index and stock layers |
| Chips | `market.db` `chip_daily`, extracted per symbol | institutional net **relative to volume**, not absolute shares |
| Macro backdrop | `market.db` `score_history`, `scope` in `macro_world`, `macro_tw` | one sentence: tailwind, headwind or neutral |
| Fundamentals | quarterly statements once stored; yfinance and FinMind are the realistic sources | revenue, margins, ROE, leverage, FCF |
| Monthly revenue (TW) | 月營收, published by the 10th for the prior month | the highest-frequency fundamental a TW name has |
| Estimates | consensus snapshot once stored | level matters less than the revision direction |
| Earnings event | report date, actual versus estimate, guidance | US: 10-Q/10-K on EDGAR, call transcript. TW: 季報 via MOPS, 法說會 where held |

Check the table exists before writing a section that depends on it. A section quietly filled with placeholders is worse than an absent one.

## 3. Note template

Written in zh-TW — the note is a deliverable a human reads, unlike this skill file.

```markdown
# <名稱>（<代號>）研究筆記 — <as_of>

## 這次有什麼不一樣
（兩到四點。只寫變了的東西：分數變化、進出某條均線、籌碼轉向、月營收或財報落地、估計值被修正。沒有變化就直說沒有變化。）

## 分數
| 維度 | 分數 | 依據 | 前一交易日 |
|---|---|---|---|
| 短期 | | | |
| 中期 | | | |
| 長期 | | | |
| 籌碼 | | | |
| 綜合 | | 可算的維度平均 | |

五日加權：<值>（10/15/20/25/30）；簡單平均：<值>

## 規則輸出的動作描述
（一句。明講這是哪一條規則的輸出。）

## 資料來源
- 價格：price_current\<SYMBOL>.csv，最後一筆 <date>
- 分數：market.db / score_history，scope=stock，as_of=<date>，price_version=<v>
- 籌碼：market.db / chip_daily <date>
- 總經背景：score_history scope=macro_world / macro_tw，as_of=<date>
- 執行紀錄：runlog\<YYYY-MM>.jsonl，run_id=<id>
```

## 4. Fundamentals and valuation — full update only

Two tables, straight from the source snapshot skill. Keep them to the columns below; a note is not a model dump.

```markdown
## 財務摘要
| 指標 | FY-2 | FY-1 | 最近四季 | 趨勢 |
|---|---|---|---|---|
| 營收 | | | | |
| 毛利率 | | | | |
| 營業利益率 | | | | |
| ROE | | | | |
| 淨負債／EBITDA | | | | |

## 估值
| 指標 | 目前 | 對照 |
|---|---|---|
| 預估本益比 | | 相對自身歷史 |
| EV/EBITDA | | 相對自身歷史 |
| 股息殖利率 | | |
```

Compare against the name's **own** history first. A peer-relative number needs a peer set, and this universe is fifteen names chosen for weight, not for comparability — 台積電 against 鴻海 is not a comps table. The ADR pairs are the exception and the most useful comparison available: 2330.TW/TSM, 2317.TW/HNHPF, 3711.TW/ASX, each leg read against its own session calendar.

Forward P/E is price over consensus EPS. When there is no stored estimate, say the multiple is trailing rather than quietly mixing the two.

## 5. Earnings update — when a report has landed

The source skill's discipline compressed to one page: lead with the variance, quantify it, explain it, then say what changed in the forward view.

```markdown
## 財報（<期別>，公布 <date>）
| 項目 | 實際 | 預估 | 差異 | 說明 |
|---|---|---|---|---|
| 營收 | | | | |
| 每股盈餘 | | | | |
| 毛利率 | | | | |

財測：<本次> vs <前次>
估計值修正：<方向與幅度>
```

Rules carried over from the source:

- Lead with beat or miss and quantify it in both currency and percent — "營收優於預估 12 億、3%" is the useful form.
- Explain **why** the number differed from the estimate; a variance without a cause is a fact, not analysis.
- Only what is new. Company background belongs in a first note, not in every update.
- Timeliness is part of the deliverable. A report note written a week late is a different document, and should say when it was written relative to the release.
- For a TW name, 月營收 arrives monthly and the statement quarterly. Say which one the note is reacting to.

## 6. Provenance

An earnings update earns trust by linking every figure to a filing. A local note earns it by pointing at local artefacts — file, table, `as_of`, `price_version`, and the `run_id` from `run_log` or `%STOCKDATA_ROOT%\runlog\<YYYY-MM>.jsonl`. A number that cannot be traced back does not go in the note; a number computed during the write-up rather than read from a run says so and names the series it came from.

Once fundamentals are stored, the same applies to them: period, statement source, and the date it was fetched. External documents get their URL — an EDGAR link for a US filing, the MOPS entry for a TW one.

## 7. Where it lands

`%STOCKDATA_ROOT%\notes\<YYYY-MM-DD>-<SYMBOL>.md`, creating `notes\` if absent.

## 8. Verification

The note is not done until these pass (global: Goal-Driven Execution):

1. Every figure in the note appears in the 資料來源 block, and re-reading one of them from the stated source reproduces the number.
2. The `as_of` shown is the one actually stored, not today's date unless they coincide and that was checked.
3. Sections 4 and 5 either ran against data confirmed to exist, or are absent — no placeholder rows.
4. Any multiple is labelled forward or trailing, matching what it was computed from.
5. The action description names the rule it came from.
6. The file landed at the path in §7.
