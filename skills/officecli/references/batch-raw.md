# officecli — Batch, dump/round-trip & L3 raw XML

Loaded on demand from `SKILL.md`. Read this before running a multi-operation batch, before a `dump → batch` round-trip, or when L2 cannot express the edit you need.

---

## batch — multiple operations in one save cycle

**Atomic by default (v1.0.137+):** every item still runs and is reported (so `N succeeded, M failed` stays meaningful and every failure surfaces), but if *any* item fails the whole batch rolls back — the file on disk is left byte-identical to before the batch ran (confirmed live in both standalone and resident mode).

- `--best-effort` restores the old apply-what-succeeds behavior. Useful for lossy `dump→batch` replays where losing the whole thing over one unsupported item is worse than a partial result.
- `--stop-on-error` only changes how early the run stops (remaining items are `skipped`), not whether what ran gets kept. Combine it with `--best-effort` for "stop at first failure but keep what already succeeded."
- `--force` is unrelated — it is only the docx-protection bypass.
- Failed items carry a machine-readable `code` field (same list as `error.code`); a rolled-back batch's JSON summary carries `"atomicRolledBack": true`.

Supports: `add`, `set`, `get`, `query`, `remove`, `move`, `swap`, `view`, `raw`, `raw-set`, `validate`.
Fields: `command` (or `op`), `path`, `parent`, `type`, `from`, `to`, `index`, `after`, `before`, `props`, `selector`, `mode`, `depth`, `part`, `xpath`, `action`, `xml`.

```bash
# bash
echo '[
  {"command":"set","path":"/Sheet1/A1","props":{"value":"Name","bold":"true"}},
  {"command":"set","path":"/Sheet1/B1","props":{"value":"Score","bold":"true"}}
]' | officecli batch data.xlsx --json

officecli batch data.xlsx --commands '[{"op":"set","path":"/Sheet1/A1","props":{"value":"Done"}}]' --json
officecli batch data.xlsx --input updates.json --best-effort --json   # keep whatever succeeds even if some items fail
```

```powershell
# PowerShell — prefer a file over piping JSON; quoting rules differ and here-strings are safest
@'
[
  {"command":"set","path":"/Sheet1/A1","props":{"value":"Name","bold":"true"}},
  {"command":"set","path":"/Sheet1/B1","props":{"value":"Score","bold":"true"}}
]
'@ | Out-File -Encoding utf8 updates.json
officecli batch data.xlsx --input updates.json --json
```

---

## dump / refresh / plugins

`officecli dump <file> [<path>]` emits a replayable batch JSON for round-trip:

- `.docx` — full coverage
- `.pptx` — text/tables/pictures/charts/notes/theme + OLE/3D/video/audio/SmartArt/morph/p15 transitions via raw-set passthrough
- `.xlsx` — cells/formulas/styles + tables, conditional formatting, validations, comments, charts, sparklines, pictures, shapes, pivot tables; slicers/chartEx/OLE via verbatim carrier

Path defaults to `/` (whole document); pass a subtree path to scope the dump — docx: `/body`, `/body/p[N]`, `/body/tbl[N]`, `/theme`, `/settings`, `/numbering`, `/styles`; xlsx: `/SheetName`, `/sheet[N]`.

`officecli refresh <file.docx>` recalculates TOC page numbers / PAGE / cross-references after replay (Word backend on Windows; headless-HTML fallback elsewhere).

`officecli plugins list` extends support to `.doc`, `.hwpx`, `.pdf` export.

---

## L3: Raw XML

Use when L2 cannot express what you need. No xmlns declarations needed — prefixes auto-registered.

```bash
officecli raw <file> <part>                          # view raw XML
officecli raw-set <file> <part> --xpath "..." --action replace --xml '<w:p>...</w:p>'
officecli add-part <file> <parent>                   # create new document part (returns rId)
```

`raw-set` actions: `append`, `prepend`, `insertbefore`, `insertafter`, `replace`, `remove`, `setattr`. Run `officecli help <format> raw` for available parts.
