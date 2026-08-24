# officecli — Batch, dump/round-trip, merge & L3 raw XML

Loaded on demand from `SKILL.md`. Read this before running a multi-operation batch, before a `dump → batch` round-trip, when filling a template, or when L2 cannot express the edit you need.

All examples are PowerShell.

## batch — multiple operations in one save cycle

**Atomic by default.** Every item runs and is reported, so `N succeeded, M failed` stays meaningful and every failure surfaces; but if *any* item fails the whole batch rolls back and the file on disk is left byte-identical to before the batch ran.

- `--best-effort` keeps whatever succeeded instead of rolling back. Use it for lossy `dump → batch` replays, where losing everything over one unsupported item is worse than a partial result.
- `--stop-on-error` only changes how early the run stops — remaining items are reported as `skipped`. It does not change whether what ran gets kept. Combine it with `--best-effort` for "stop at the first failure but keep what already succeeded."
- `--force` is unrelated: it is only the docx-protection bypass.
- Failed items carry a machine-readable `code` field (the same list as `error.code`). A rolled-back batch's JSON summary carries `"atomicRolledBack": true`.

Supports: `add`, `set`, `get`, `query`, `remove`, `move`, `swap`, `view`, `raw`, `raw-set`, `validate`.

Fields: `command` (or `op`), `path`, `parent`, `type`, `from`, `to`, `index`, `after`, `before`, `props`, `selector`, `mode`, `depth`, `part`, `xpath`, `action`, `xml`.

**Write the JSON to a UTF-8 file and pass `--input`.** Do not pipe it: `$OutputEncoding` defaults to ASCII in Windows PowerShell and silently replaces every non-ASCII character with `?` on its way into a native command.

```powershell
@'
[
  {"command":"set","path":"/Sheet1/A1","props":{"value":"Name","bold":"true"}},
  {"command":"set","path":"/Sheet1/B1","props":{"value":"Score","bold":"true"}}
]
'@ | Out-File -Encoding utf8 updates.json

officecli batch data.xlsx --input updates.json --json
officecli batch data.xlsx --input updates.json --best-effort --json   # keep whatever succeeds
```

For a one-liner with no non-ASCII content, `--commands` takes the JSON inline:

```powershell
officecli batch data.xlsx --commands '[{"op":"set","path":"/Sheet1/A1","props":{"value":"Done"}}]' --json
```

## dump / refresh / plugins

`officecli dump <file> [<path>]` emits a replayable batch JSON for round-tripping:

- `.docx` — full coverage
- `.pptx` — text, tables, pictures, charts, notes, theme; OLE, 3D models, video/audio, SmartArt, and morph transitions pass through via `raw-set`
- `.xlsx` — cells, formulas, styles, tables, conditional formatting, validations, comments, charts, sparklines, pictures, shapes, pivot tables; slicers, chartEx, and OLE ride along as verbatim carriers

Path defaults to `/` (whole document); pass a subtree path to scope the dump — docx: `/body`, `/body/p[N]`, `/body/tbl[N]`, `/theme`, `/settings`, `/numbering`, `/styles`; xlsx: `/SheetName`, `/sheet[N]`.

`officecli refresh <file.docx>` recalculates TOC page numbers, `PAGE` fields, and cross-references after a replay. On Windows it drives the Word backend.

`officecli plugins list` shows the installed format handlers, which extend support to `.doc`, `.hwpx`, and PDF export.

## merge — fill a template

`officecli merge` replaces `{{key}}` placeholders throughout a document from a JSON data file. Use it instead of a long `batch` of `set --find/--replace` when the document was authored as a template.

```powershell
@'
{ "client": "Acme Corp", "quarter": "Q4", "total": "1,240,000" }
'@ | Out-File -Encoding utf8 data.json

officecli merge template.docx --data data.json
```

## L3: Raw XML

Use when L2 cannot express what you need. No `xmlns` declarations are needed — prefixes are auto-registered.

```powershell
officecli raw <file> <part>                          # view raw XML
officecli raw-set <file> <part> --xpath "..." --action replace --xml '<w:p>...</w:p>'
officecli add-part <file> <parent>                   # create a new document part (returns rId)
```

`raw-set` actions: `append`, `prepend`, `insertbefore`, `insertafter`, `replace`, `remove`, `setattr`. Run `officecli help <format> raw` for the available parts.

After any L3 edit, run `officecli validate <file>` — raw XML bypasses the schema checks that L2 applies for you.
