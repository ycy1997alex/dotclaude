# officecli — Element types & format-specific operations

Loaded on demand from `SKILL.md`. Read this when you need to know which element types exist for a format, or need pivot tables / document-level properties / sort / anchored insert.

**When unsure about a property name, run `officecli help <format> <element>` instead of reading this table top to bottom.** This file is the map; `help` is the authority.

---

## Element types (with aliases)

### pptx

slide (incl. hidden), shape (font.latin/ea/cs, direction=rtl, underline.color, highlight=COLOR (Add/Set/Get/HTML preview), effective.X+effective.X.src; arrow alias for rightArrow; slideMaster/slideLayout typed add/set/remove), picture (SVG, brightness/contrast/glow/shadow, rotation, link, tooltip), chart (direction=rtl, pieOfPie, barOfPie, axisLine/gridline per-attr setters, animation+chartBuild=byCategory|bySeries, line dropLines/hiLowLines/upDownBars, anchor=x,y,w,h shorthand), table (cell direction=rtl, fill/background, built-in PowerPoint style catalogue, /col[C] get + swap/copyFrom, row/col Move/CopyFrom), row (tr), connector (from/to accept full-path `@name=`/`@id=` forms — bare `@name=Foo` is rejected, must be `/slide[N]/shape[@name=Foo]` — startshape/endshape SetByPath; edge-to-edge anchoring by default, fromSide/toSide to force an edge, fromIdx/toIdx for raw cxn index), group (link, tooltip, deep walk by get/query/add/remove, ungroup=true dissolves back to slide-absolute), align/distribute (targets= accepts shape[@id=N] paths, not just positional), video/audio (loop, autoStart alias), equation, notes (direction=rtl, lang), comment (legacy + modern p188 threaded round-trip), animation (15 emphasis + 16 exit presets, multi-effect chains, motion-path presets, repeat/restart/autoReverse, chart animations), transition (12 p15 presets + morph/p14), paragraph (para), run, zoom, ole (preview=, full dump round-trip via add-part+raw-set), placeholder (phType=...), model3d (rotation=ax,ay,az; full dump round-trip), smartart (dump round-trip via add-part), diagram (add-only mermaid → native shapes or rendered image, `--type diagram`/`flowchart`).

### docx

paragraph (direction/font.latin/ea/cs, bold.cs/italic.cs/size.cs, lang.latin/ea/cs, wordWrap, framePr.\*, tabs shorthand), run (lang slots, direction, underline.color, position half-pts, **revision.type=ins\|del\|format\|moveFrom\|moveTo + revision.action=accept\|reject** with .author/.date — bare `@author=`/`@type=` selector on `set /revision[...]` for filtered accept/reject, but `query 'revision[...]'` needs the dotted `revision.author=`/`revision.type=` form; move+revision is run-level paths only, not paragraph-level; **range=START:END** on a paragraph/shape path formats a char span by explicit 0-based half-open offset instead of addressing a run — the offset sibling of find=), table (direction=rtl, hMerge, cantSplit on row/nowrap on cell (both add+set), **virtual column ops**: add/remove/move/copyfrom on /body/tbl[N]/col), row (tr), cell (td), image, header/footer (direction), section (pageNumFmt full enum, direction=rtl, rtlGutter, pgBorders=box), bookmark, comment, footnote, endnote, formfield, sdt, chart, equation, field (28 types), hyperlink, style (direction, indents, pbdr, lineSpacing on Add/Set), toc, watermark, break, ole, **num/abstractNum/lvl**, **tab**, **textbox/shape** (add-mostly — Get returns raw XML preview only, no structured readback; Set is limited to width/height/geometry/fill/line.\*; position is `anchor.x`/`anchor.y` not bare x/y; **textbox-only** `textDirection`/rotation/gradient/shadow — docx shape itself has neither rotation nor gradient), embedded **OLE round-trip on dump→batch**, **diagram** (add-only mermaid → native shapes or rendered image, `--type diagram`/`flowchart`, no x/y at add-time — reposition via `set /body/group[N]`). docDefaults.rtl, autoHyphenation, `get /` exposes locale + /comments /footnotes /endnotes. `create --minimal` for raw OOXML scaffolding.

### xlsx

sheet (visible/hidden/veryHidden, print margins, printTitleRows/Cols, rightToLeft sheetView, cascade-aware rename), row (c{N}= cell-content shorthand; add accepts --from /Sheet/col[L]; formula-ref rewrite on insert), col (formula-ref rewrite, named-range follow on move), cell (type=richtext+runs, merge=range/sweep, direction=rtl, phonetic; **--shift left\|up on remove, shift=right\|down on add** — Excel UI dialog parity; formula auto-detect; OFFSET/INDIRECT in calc), chart (per-axis RTL/title, anchor=x,y,w,h, pareto), image (SVG), comment (direction=rtl), table (listobject), namedrange (definedname, volatile, `[@name=X]`; formula-body inlined at parse), pivottable (cache CoW + cross-pivot sharing, labelFilter=field:type:value add-time-only, topN=integer add-time-only, fillDownLabels is an alias of repeatLabels not a separate feature, calculatedField), sparkline, validation, autofilter, shape, textbox, CF (databar/colorscale/iconset/formulacf/cellIs/topN/aboveAverage), ole, csv. Query supports `merge`/`mergedrange`. Workbook: password. Shape selector enumerates leaves inside grpSp.

---

## Pivot tables (xlsx)

```bash
officecli add data.xlsx /Sheet1 --type pivottable \
  --prop source="Sheet1!A1:E100" --prop rows=Region,Category \
  --prop cols=Year --prop values="Sales:sum,Qty:count" \
  --prop grandTotals=rows --prop subtotals=off --prop sort=asc
```

Key props: `rows`, `cols`, `values` (Field:func[:showDataAs]), `filters`, `source`, `position`, `layout` (compact/outline/tabular), `repeatLabels`, `blankRows`, `aggregate`, `showDataAs` (percent_of_total/row/col, running_total), `grandTotals`, `subtotals`, `sort`. Aggregators: sum, count, average, max, min, product, stdDev, stdDevp, var, varp, countNums. Date columns auto-group. Run `officecli help xlsx pivottable` for full schema.

---

## Document-level properties (all formats)

```bash
officecli set doc.docx / --prop docDefaults.font=Arial --prop docDefaults.fontSize=11pt
officecli set doc.docx / --prop protection=forms --prop evenAndOddHeaders=true
officecli set data.xlsx / --prop calc.mode=manual --prop calc.refMode=r1c1
officecli set slides.pptx / --prop defaultFont=Arial --prop show.loop=true --prop print.what=handouts
```

Run `officecli help <format> /` for all document-level properties (docDefaults, docGrid, CJK spacing, calc, print, show, theme, extended).

---

## Sort (xlsx)

```bash
officecli set data.xlsx /Sheet1 --prop sort="C desc" --prop sortHeader=true
officecli set data.xlsx '/Sheet1/A1:D100' --prop sort="A asc" --prop sortHeader=true
```

Format: `COL DIR[, COL DIR ...]`. Rejects ranges with merged cells or formulas. Sidecar metadata (hyperlinks, comments, conditional formatting, drawings) follows rows automatically.

---

## Text-anchored insert (`--after find:X` / `--before find:X`)

Locate an insertion point by text match within a paragraph. Inline types (run, picture, hyperlink) insert within the paragraph; block types (table, paragraph) auto-split it. PPT only supports inline.

```bash
# Word: inline run after matched text
officecli add doc.docx '/body/p[1]' --type run --after find:weather --prop text=" (sunny)"

# Word: block table after matched text (auto-splits paragraph)
officecli add doc.docx '/body/p[1]' --type table --after "find:First sentence." --prop rows=2 --prop cols=2
```

---

## Clone

`officecli add <file> / --from '/slide[1]'` — copies with all cross-part relationships.
