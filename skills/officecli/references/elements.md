# officecli — Element types & format-specific operations

Loaded on demand from `SKILL.md`. Read this when you need to know which element types exist for a format, or need pivot tables / document-level properties / sort / anchored insert / clone.

**When unsure about a property name, run `officecli help <format> <element>` instead of reading this file top to bottom.** This file is the map; `help` is the authority.

All examples are PowerShell.

## Element types

### pptx

| Type (aliases) | Notes |
|---|---|
| `slide` | Hidden slides included. `slideMaster` / `slideLayout` are separately addressable. |
| `shape` | `font.latin` / `font.ea` / `font.cs` per script; `highlight=COLOR`; `effective.X` reads the resolved value and `effective.X.src` says where it came from. |
| `picture` | SVG supported. `brightness`, `contrast`, `glow`, `shadow`, `rotation`, `link`, `tooltip`. |
| `chart` | `anchor=x,y,w,h` shorthand. Per-attribute axis and gridline setters. Pie-of-pie and bar-of-pie. |
| `table`, `row` (`tr`) | Built-in PowerPoint style catalogue. `/col[C]` addressable for get / swap / copyFrom. |
| `connector` | `from` / `to` need a full path — `/slide[N]/shape[@name=Foo]`. A bare `@name=Foo` is rejected. Edge-to-edge anchoring by default; `fromSide` / `toSide` force a specific edge. |
| `group` | `get` / `query` / `add` / `remove` walk into it. `ungroup=true` dissolves it back to slide-absolute coordinates. |
| `align` / `distribute` | `targets=` accepts `shape[@id=N]` paths, not only positional ones. |
| `video`, `audio` | `loop`, `autoStart`. |
| `animation`, `transition` | Emphasis, exit, and motion-path presets; multi-effect chains; `repeat` / `restart` / `autoReverse`; chart build order. Morph transition supported. |
| `paragraph` (`para`), `run` | Text inside a shape. |
| `notes`, `comment` | Threaded comments round-trip. |
| `equation`, `zoom`, `placeholder` (`phType=`), `ole`, `model3d`, `smartart` | `model3d` takes `rotation=ax,ay,az`. |
| `diagram` / `flowchart` | Add-only: Mermaid source becomes native shapes or a rendered image. |

### docx

| Type (aliases) | Notes |
|---|---|
| `paragraph` | `direction`, per-script `font.latin` / `.ea` / `.cs`, `bold.cs` / `italic.cs` / `size.cs`, `lang.*`, `wordWrap`, `framePr.*`, `tabs` shorthand. |
| `run` | Per-script `lang` slots, `direction`, `underline.color`, `position` in half-points. `range=START:END` on a paragraph path formats a character span by 0-based half-open offset — the offset-based sibling of `--find`. |
| revisions | `revision.type=ins\|del\|format\|moveFrom\|moveTo` plus `revision.action=accept\|reject`, with `.author` / `.date`. On `set /revision[...]` a bare `@author=` / `@type=` selector filters; on `query 'revision[...]'` use the dotted `revision.author=` / `revision.type=` form. Move revisions are run-level paths only. |
| `table`, `row` (`tr`), `cell` (`td`) | `hMerge`, `cantSplit` on row, `nowrap` on cell. Virtual column ops — add / remove / move / copyFrom on `/body/tbl[N]/col`. |
| `section` | Full `pageNumFmt` enum, `direction=rtl`, `rtlGutter`, `pgBorders=box`. |
| `header`, `footer` | `direction`. |
| `image`, `chart`, `equation`, `watermark`, `break`, `ole` | |
| `bookmark`, `hyperlink`, `field`, `toc` | `field` covers 28 field types. |
| `comment`, `footnote`, `endnote` | `get /` exposes `/comments`, `/footnotes`, `/endnotes`. |
| `formfield`, `sdt` | Content controls. |
| `style` | `direction`, indents, `pbdr`, `lineSpacing` on both add and set. |
| `num` / `abstractNum` / `lvl`, `tab` | List numbering definitions. |
| `textbox` / `shape` | Add-mostly. `get` returns a raw XML preview, not a structured readback. `set` is limited to width / height / geometry / fill / `line.*`. Position is `anchor.x` / `anchor.y`, not bare `x` / `y`. `textDirection`, `rotation`, `gradient`, and `shadow` work on `textbox` only — a docx `shape` has neither rotation nor gradient. |
| `diagram` / `flowchart` | Add-only Mermaid, and no `x` / `y` at add time — reposition afterwards with `set /body/group[N]`. |

Document-level: `docDefaults.rtl`, `autoHyphenation`. `create --minimal` produces raw OOXML scaffolding.

### xlsx

| Type (aliases) | Notes |
|---|---|
| `sheet` | `visible` / `hidden` / `veryHidden`, print margins, `printTitleRows` / `printTitleCols`, `rightToLeft` sheet view. Rename cascades to formulas that reference the sheet. |
| `row` | `c{N}=` cell-content shorthand. `add` accepts `--from /Sheet/col[L]`. Formula references are rewritten on insert. |
| `col` | Formula references rewritten; named ranges follow on move. |
| `cell` | `type=richtext` with runs, `merge=range\|sweep`, `direction=rtl`, phonetic. `--shift left\|up` on remove and `shift=right\|down` on add. Formulas are auto-detected; `OFFSET` / `INDIRECT` resolve in calc. |
| `chart` | Per-axis RTL and title, `anchor=x,y,w,h`, Pareto. |
| `pivottable` | See below. |
| `table` (listobject), `namedrange` (`definedname`) | `namedrange` supports `volatile` and `[@name=X]`. |
| `sparkline`, `validation`, `autofilter` | |
| `CF` | Conditional formatting: databar, colorscale, iconset, formula, cellIs, topN, aboveAverage. |
| `image`, `comment`, `shape`, `textbox`, `ole`, `csv` | The shape selector enumerates leaves inside grouped shapes. |

`query` supports `merge` / `mergedrange`. Workbook-level: `password`.

## Pivot tables (xlsx)

```powershell
officecli add data.xlsx /Sheet1 --type pivottable `
  --prop source="Sheet1!A1:E100" --prop rows=Region,Category `
  --prop cols=Year --prop values="Sales:sum,Qty:count" `
  --prop grandTotals=rows --prop subtotals=off --prop sort=asc
```

Key props: `rows`, `cols`, `values` (`Field:func[:showDataAs]`), `filters`, `source`, `position`, `layout` (compact/outline/tabular), `repeatLabels`, `blankRows`, `aggregate`, `showDataAs` (percent_of_total/row/col, running_total), `grandTotals`, `subtotals`, `sort`, `calculatedField`. Aggregators: sum, count, average, max, min, product, stdDev, stdDevp, var, varp, countNums. Date columns auto-group. `labelFilter=field:type:value` and `topN=<integer>` can only be set at add time. Run `officecli help xlsx pivottable` for the full schema.

## Document-level properties (all formats)

```powershell
officecli set doc.docx / --prop docDefaults.font=Arial --prop docDefaults.fontSize=11pt
officecli set doc.docx / --prop protection=forms --prop evenAndOddHeaders=true
officecli set data.xlsx / --prop calc.mode=manual --prop calc.refMode=r1c1
officecli set slides.pptx / --prop defaultFont=Arial --prop show.loop=true --prop print.what=handouts
```

Run `officecli help <format> /` for all document-level properties (docDefaults, docGrid, CJK spacing, calc, print, show, theme, extended).

## Sort (xlsx)

```powershell
officecli set data.xlsx /Sheet1 --prop sort="C desc" --prop sortHeader=true
officecli set data.xlsx '/Sheet1/A1:D100' --prop sort="A asc" --prop sortHeader=true
```

Format: `COL DIR[, COL DIR ...]`. Rejects ranges with merged cells or formulas. Sidecar metadata (hyperlinks, comments, conditional formatting, drawings) follows rows automatically.

## Text-anchored insert (`--after find:X` / `--before find:X`)

Locate an insertion point by text match within a paragraph. Inline types (run, picture, hyperlink) insert within the paragraph; block types (table, paragraph) auto-split it. PPT supports inline only.

```powershell
# Word: inline run after matched text
officecli add doc.docx '/body/p[1]' --type run --after find:weather --prop text=" (sunny)"

# Word: block table after matched text (auto-splits the paragraph)
officecli add doc.docx '/body/p[1]' --type table --after "find:First sentence." --prop rows=2 --prop cols=2
```

## Clone

```powershell
officecli add slides.pptx / --from '/slide[1]'
```

Copies the element with all its cross-part relationships (images, charts, embedded objects).
