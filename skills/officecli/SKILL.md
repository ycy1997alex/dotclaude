---
name: officecli
description: Creates, analyzes, proofreads, and modifies Office documents (.docx, .xlsx, .pptx) through the officecli CLI tool. Triggers when the user wants to create, inspect, check formatting, find issues, add charts, or modify .docx / .xlsx / .pptx files.
---

# officecli

AI-friendly CLI for .docx, .xlsx, .pptx. Single binary, no dependencies, no Office installation needed. All examples in this file are PowerShell, the shell on this machine (global: Security & Environment).

## Install

Check first with `officecli --version`.

**Never install it on your own initiative.** If the check fails, stop and ask the user for explicit permission before running anything — the one-line installers below pipe a remote script straight into a shell, so their contents can change at any time and are not verified against a checksum or signature. State that in the request, show the exact command, and wait for a yes. If the user declines, report that officecli is unavailable rather than looking for another way to install it.

Once the user has approved, on Windows:

```powershell
irm https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 | iex
```

Package managers avoid the pipe-to-shell problem entirely and are the better offer when the user has one:

```powershell
scoop install officecli
npm install -g @officecli/officecli
```

Verify with `officecli --version`. If still not found after install, open a new terminal.

## Strategy

**L1 (read) → L2 (DOM edit) → L3 (raw XML)**. Always prefer higher layers. Add `--json` for structured output.

**Before doc work, check Specialized Skills** (bottom of this file). Fundraising decks, academic papers, financial models, dashboards, and Morph animations need their own skill loaded first — run `officecli load_skill <name>` once, then proceed.

## Help System (IMPORTANT)

**When unsure about property names, value formats, or command syntax, ALWAYS run help instead of guessing.** One help query beats guess-fail-retry loops.

`officecli help` ≡ `officecli --help`, and `officecli <cmd> --help` ≡ `officecli help <cmd>` — same content.

```powershell
officecli help                                  # All commands + global options + schema entry points
officecli help docx                             # List all docx elements
officecli help docx paragraph                   # Full schema: properties, aliases, examples, readbacks
officecli help docx set paragraph               # Verb-filtered: only props usable with `set`
officecli help docx paragraph --json            # Structured schema (machine-readable)
```

Format aliases: `word`→`docx`, `excel`→`xlsx`, `ppt`/`powerpoint`→`pptx`. Verbs: `add`, `set`, `get`, `query`, `remove`. MCP exposes the same schema via the single `command` string param: `{"command":"help docx paragraph"}` — the MCP tool has exactly one param and passes it to the CLI verbatim.

## Performance: Resident Mode

**Every command auto-starts a resident on first access** — file-lock conflicts are automatically avoided. Explicit `open`/`close` is still recommended for longer sessions:

```powershell
officecli open report.docx       # explicitly keep in memory
officecli set report.docx ...    # no file I/O overhead
officecli close report.docx      # save and release
```

Opt out of auto-start: `$env:OFFICECLI_NO_AUTO_RESIDENT = '1'`.

**Flush only at the non-officecli boundary.** officecli's own reads (`get`/`query`/`view`/`dump`) always see your latest edits, so you never need to save mid-workflow. Run `save` (keeps the resident) or `close` (flush + release) only **before a non-officecli program reads the file** — python-docx/openpyxl, Word, a renderer, delivery/upload. Idle sessions auto-flush on their own; `$env:OFFICECLI_RESIDENT_FLUSH = 'each'` makes every mutation flush before returning.

## Quick Start

**PPT:**

```powershell
officecli create slides.pptx
officecli add slides.pptx / --type slide --prop title="Q4 Report" --prop background=1A1A2E
officecli add slides.pptx '/slide[1]' --type shape --prop text="Revenue grew 25%" --prop x=2cm --prop y=5cm --prop font=Arial --prop size=24 --prop color=FFFFFF
```

**Word:**

```powershell
officecli create report.docx
officecli add report.docx /body --type paragraph --prop text="Executive Summary" --prop style=Heading1
officecli add report.docx /body --type paragraph --prop text="Revenue increased by 25% year-over-year."
```

**Excel:**

```powershell
officecli create data.xlsx
officecli set data.xlsx /Sheet1/A1 --prop value="Name" --prop bold=true
officecli set data.xlsx /Sheet1/A2 --prop value="Alice"
```

## L1: Create, Read & Inspect

```powershell
officecli create <file>               # Create blank .docx/.xlsx/.pptx (type from extension)
officecli view <file> <mode>          # outline | stats | issues | text | annotated | html
officecli get <file> <path> --depth N # Get a node and its children [--json]
officecli query <file> <selector>     # CSS-like query
officecli validate <file>             # Validate against OpenXML schema
```

### view modes

| Mode | Description | Useful flags |
|------|-------------|-------------|
| `outline` | Document structure | |
| `stats` | Statistics (pages, words, shapes) | |
| `issues` | Formatting/content/structure problems | `--type format\|content\|structure`, `--limit N` |
| `text` | Plain text extraction | `--start N --end N`, `--max-lines N` |
| `annotated` | Text with formatting annotations | |
| `html` | Static HTML snapshot — same renderer as `watch`, no server needed | `--browser`, `--page N` (docx), `--start N --end N` (pptx) |
| `screenshot` / `svg` / `pdf` / `forms` | PNG via headless browser / SVG (pptx slide) / PDF via exporter plugin / form-fields JSON via format-handler plugin | `-o`, `--screenshot-width/-height`, pptx `--grid N` |

Use `view html` for one-shot snapshots (CI artifacts, archival, diffing); use `watch` when you need live refresh or browser-side click-to-select.

### get

Any XML path via element localName. Use `--depth N` to expand children. Add `--json` for structured output. Default text output is grep-friendly: `path (type) "text" key=val key=val ...`

```powershell
officecli get report.docx '/body/p[3]' --depth 2 --json
officecli get slides.pptx '/slide[1]' --depth 1          # list all shapes on slide 1
officecli get data.xlsx '/Sheet1/B2' --json
```

### Stable ID Addressing

Elements with stable IDs return `@attr=value` paths instead of positional indices. Prefer these in multi-step workflows — positional indices shift on insert/delete, stable IDs do not.

```
/slide[1]/shape[@id=550950021]                    # PPT shape
/slide[1]/table[@id=1388430425]/tr[1]/tc[2]       # PPT table
/body/p[@paraId=1A2B3C4D]                         # Word paragraph
/comments/comment[@commentId=1]                    # Word comment
```

PPT also accepts `@name=` (e.g. `shape[@name=Title 1]`). Elements without stable IDs (slide, run, tr/tc, row) fall back to positional indices.

### query

CSS-like selectors: `[attr=value]`, `[attr!=value]`, `[attr~=text]`, `[attr>=value]`, `[attr<=value]`, `:contains("text")`, `:empty`, `:has(formula)`, `:no-alt`. Boolean `and`/`or` works across `query`/`set`/`remove`: `cell[value>5000 or value<100]`, `cell[(type=Number or type=Date) and value>0]`. Excel row-by-column-name: `Sheet1!row[Salary>5000]`. `set` accepts selectors and Excel-native paths. Bare unscoped selectors are rejected on `set`/`remove`.

```powershell
officecli query report.docx 'paragraph[style=Normal] > run[font!=Arial]'
officecli query slides.pptx 'shape[fill=FF0000]'
```

## L2: DOM Operations

### set — modify properties

```powershell
officecli set <file> <path> --prop key=value [--prop ...]
```

**Any XML attribute is settable** via element path (found via `get --depth N`) — even attributes not currently present. Without `--find`, `set` applies format to the entire element.

**Value formats:**

| Type | Format | Examples |
|------|--------|---------|
| Colors | Hex (with/without `#`), named, RGB, theme | `FF0000`, `#FF0000`, `red`, `rgb(255,0,0)`, `accent1`..`accent6` |
| Spacing | Unit-qualified | `12pt`, `0.5cm`, `1.5x`, `150%` |
| Dimensions | EMU or suffixed | `914400`, `2.54cm`, `1in`, `72pt`, `96px` |

**Dotted-attr aliases** — `font.<attr>` forms accepted on shape/run/paragraph/table/row/cell/section/styles, e.g. `--prop font.color=red --prop font.bold=true --prop font.size=14pt`. Run `officecli help <fmt> <element>` for the full list.

### find — format or replace matched text

Use top-level `--find` / `--replace` on `set` (and `--find` on `query`).

```powershell
# Format matched text (auto-splits runs)
officecli set doc.docx '/body/p[1]' --find weather --prop bold=true --prop color=red

# Regex matching (regex= is a prop flag)
officecli set doc.docx '/body/p[1]' --find '\d+%' --prop regex=true --prop color=red

# Replace text (use `/` for whole-document scope)
officecli set doc.docx / --find draft --replace final

# docx: tracked Find&Replace
officecli set doc.docx / --find draft --replace final --prop revision.author=Alice

# PPT — same syntax, different paths
officecli set slides.pptx / --find draft --replace final
```

**Path controls search scope:** `/` = whole document, `/body/p[1]` or `/slide[N]/shape[M]` = specific element, `/header[1]` / `/footer[1]` = headers/footers.

**Notes:**

- Case-sensitive by default. Case-insensitive: `--find '(?i)error' --prop regex=true`
- Matches work across run boundaries
- No match = silent success. `--json` includes `"matched": N`
- **Excel:** only `find` + `replace` supported (no find + format props)

### add — add elements or clone

```powershell
officecli add <file> <parent> --type <type> [--prop ...]
officecli add <file> <parent> --type <type> --after <path> [--prop ...]   # insert after anchor
officecli add <file> <parent> --type <type> --before <path> [--prop ...]  # insert before anchor
officecli add <file> <parent> --type <type> --index N [--prop ...]        # 0-based position
officecli add <file> <parent> --from <path>                               # clone existing element
```

`--after`, `--before`, `--index` are mutually exclusive. No position flag = append to end.

For the element types available per format, and for pivot tables, sort, document-level properties, text-anchored insert, and clone semantics, see `references/elements.md`.

### move, swap, remove

```powershell
officecli move <file> <path> [--to <parent>] [--index N] [--after <path>] [--before <path>]
officecli swap <file> <path1> <path2>
officecli remove <file> '/body/p[4]'
```

When using `--after` or `--before`, `--to` can be omitted — the target container is inferred from the anchor.

## References

Read one of these only when the task actually reaches it — they are not part of the default workflow:

- `references/elements.md` — read when you need the element types available for a format, or are building a pivot table, sorting a sheet, setting document-level properties, inserting at a text anchor, or cloning an element.
- `references/watch-marks.md` — read when the user wants a live browser preview, wants to click shapes and have you act on the selection, or wants edits staged for review instead of written straight to the file.
- `references/batch-raw.md` — read when applying many operations in one save cycle, round-tripping a document through `dump`, merging template placeholders, or dropping to raw XML because L2 cannot express the change.

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| `--name "foo"` | Use `--prop name="foo"` — all attributes go through `--prop` |
| `$` inside a double-quoted string | PowerShell interpolates `$`. Use single quotes: `--prop text='$15M'` |
| Piping JSON into `officecli batch` | `$OutputEncoding` defaults to ASCII and mangles non-ASCII. Write a UTF-8 file and pass `--input` |
| PPT `shape[1]` for content | `shape[1]` is typically the title placeholder. Use `shape[2]+` for content shapes |
| `/shape[myname]` | Name indexing not supported. Use numeric index or `@name=` (PPT only) |
| Guessing property names | Run `officecli help <format> <element>` to see exact names |
| Modifying an open file | Close the file in PowerPoint/Word/Excel first |
| `\n` in shell strings | Use `` `n `` in a PowerShell double-quoted string, or `\\n` inside `--prop text="..."` |

## Specialized Skills

`officecli load_skill <name>` — output is a SKILL.md, follow its rules.

**Loading rule**:

- Pick the most specific match in "When to use"; if none fits, load the format default (`word` / `pptx` / `excel`).
- Scenes already contain the format default's rules — load **one** skill per artifact, never stack.
- Loaded rules persist across turns; don't re-load each reply.
- Two distinct artifacts → two separate loads.

### Word (.docx)

| Name | When to use |
|------|-------------|
| `word` | Reports, letters, memos, proposals, generic documents |
| `academic-paper` | Journal / conference / thesis: APA / Chicago / IEEE / MLA citations, equations, SEQ + PAGEREF cross-refs, multi-column journal layout, bibliography. NOT for business reports or letters (route those to `word`) |

### PowerPoint (.pptx)

| Name | When to use |
|------|-------------|
| `pptx` | Generic decks: board reviews, sales decks, all-hands, product launches |
| `pitch-deck` | **Fundraising only** — seed / Series A-C / SAFE / convertible / strategic raise. NOT for sales / product / board decks (route those to `pptx`) |
| `morph-ppt` | Cinematic Morph-animated presentations. NOT for static decks (route those to `pptx`) |
| `morph-ppt-3d` | 3D Morph: GLB models, camera moves, depth. NOT for 2D-only Morph (route those to `morph-ppt`) |

### Excel (.xlsx)

| Name | When to use |
|------|-------------|
| `excel` | Generic workbooks, formulas, pivots, trackers |
| `financial-model` | Financial models, scenarios, projections. NOT for general data analysis (route those to `excel`) |
| `data-dashboard` | CSV/tabular data → KPI / analytics / executive dashboards with charts and sparklines. NOT for raw data tracking (route those to `excel`) |

Example: a fundraising deck task → `officecli load_skill pitch-deck` → use the printed rules.

## Notes

- Paths are **1-based** (XPath convention): `'/body/p[3]'` = third paragraph
- `--index` is **0-based** (array convention): `--index 0` = first position
- **Excel exception**: for `add --type row` and `add --type col`, `--index N` is **1-based** (matches OOXML RowIndex / column letter index). `--index 5` inserts at row 5 / column 5.
- **When unsure**, run `officecli help <format> <element>` instead of guessing

## Verification

A document is not done because the command exited zero (global: Goal-Driven Execution):

1. `officecli validate <file>` returns clean.
2. `officecli view <file> issues` reports nothing new that this task introduced.
3. Read the change back with `get` or `query` and confirm it is what was asked for — `set` reports success on zero matches.
4. If the file will be opened by a non-officecli program, run `officecli close <file>` first, then confirm the file on disk reflects the edit.
5. For anything visual (slides, charts, layout), render it — `officecli view <file> screenshot -o check.png` — and look at the image.
