# officecli — Watch, interactive selection & marks

Loaded on demand from `SKILL.md`. Read this when the user wants a live preview, wants to click elements in a browser and have you act on the selection, or wants edit proposals held for review instead of written straight to the file.

All examples are PowerShell.

## Watch

Live HTML preview that auto-refreshes on every file change. The browser can click / shift-click / box-drag to select shapes; the CLI can read the current browser selection and act on it.

```powershell
officecli watch <file> [--port N]      # Start preview server (default port 26315)
officecli unwatch <file>               # Stop
officecli goto <file> <path>           # Scroll watching browser(s) to element (docx: p / table / tr / tc)
```

Open the printed `http://localhost:N` URL. Click to select; shift+click or ctrl+click to multi-select; drag from empty space to box-select. PPT and Word use a blue outline; Excel uses a native-style green selection (double-click a cell to edit inline; drag a chart to reposition).

Use `view html` for one-shot snapshots (CI artifacts, archival, diffing); use `watch` when you need live refresh or browser-side click-to-select.

## `get <file> selected` — read what the user clicked

```powershell
officecli get <file> selected [--json]
```

Returns DocumentNodes for whatever is currently selected. Empty result if nothing is selected. Exit code is non-zero if no watch is running.

```powershell
# The user clicks shapes in the browser, then asks "make these red"
$selected = officecli get deck.pptx selected --json | ConvertFrom-Json
$selected.data.Results | ForEach-Object { officecli set deck.pptx $_.path --prop fill=FF0000 }
```

### Key properties

- **Selection survives file edits.** Paths use the stable `@id=` form.
- **All connected browsers share one selection.** Last write wins.
- **One watch per file.** A given file can have only one watch process at a time.
- **Group shapes select as a whole.** Drilling into individual children of a group is not supported.
- **Coverage:** `.pptx` shapes, pictures, tables, charts, connectors, and groups; `.docx` top-level paragraphs and tables. Inherited layout/master decorations and Word nested elements (table cells, run-level) are not addressable. `.xlsx` does not emit `data-path`, so `mark` and `selection` on a workbook always resolve as `stale=true` — use paths directly there instead.

## Marks — edit proposals waiting for review

Use `mark` when changes need human review BEFORE they hit the file. Marks live in the watch process only; a separate `set` pipeline applies the accepted ones. For one-shot changes use `set` directly; for permanent file annotations use `add --type comment` (Word native).

```powershell
officecli mark <file> <path> [--prop find=... color=... note=... tofix=... regex=true] [--json]
officecli unmark <file> [--path <p> | --all] [--json]
officecli get-marks <file> [--json]
```

Props:

- `find` — literal, or regex when `regex=true`. Raw form: `find='r"[abc]"'`.
- `color` — hex, `rgb(...)`, or one of the named colours in the whitelist.
- `note` — the reviewer-facing text.
- `tofix` — drives the apply pipeline.

**Path** must be the `data-path` format taken from the watch HTML. Run `officecli load_skill <format>` for the full apply pipeline.
