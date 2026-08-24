# dotclaude

[繁體中文](README.md) | English

## Overview

This repo is a **user-scope configuration set for Claude Code**. Its contents are deployed into the home directory at `~/.claude/`, serving Claude Desktop, Claude Code inside VS Code, and terminal Claude Code from a single source. There is no executable code — the deliverables are markdown rule files plus one JSON settings file: a global behaviour charter (`CLAUDE.md`), 8 skills, 3 rules, 1 subagent, and the permission/model configuration in `settings.json`.

Two directories take no part in deployment and affect no model behaviour: `含中文翻譯/` ("with Chinese translation") holds a human-facing mirror and its translations, and `.ref/` keeps superseded charters for reference. `skills/synced/` is a backup of skills synced from the claude.ai account — not content this repo maintains.

## Architecture

The real architecture is *which file loads when*. Claude Code has four loading tiers, and this repo's directory layout maps directly onto them:

| Tier | Files | Loads when | Cost |
| --- | --- | --- | --- |
| Always in context | `CLAUDE.md` | Every session, every project, from the first turn | Paid on every conversation |
| On file type | `rules/*.md` | The task touches a file matching the rule's `paths:` glob | Paid only when relevant |
| On task match | `skills/*/SKILL.md` | The `description` matches the request, or the user types `/<name>` | Only the description is resident; the body loads on demand |
| On invocation | `agents/*.md` | The main session calls the Agent tool with that `subagent_type` | Isolated context, no pollution of the main thread |

A skill carrying `paths:` picks up one further restriction: **it loads only after the model has actually touched a matching file**, so it is absent from the skill listing at the start of a session. That is a deliberate trade. It suits work that always begins from an existing file (`python-ui`) and hurts work where the user speaks before any file is open, which is why `python-plot` drops `paths:` and triggers on its description instead.

A skill's `references/` directory is the third disclosure tier: the SKILL.md body loads in full when the skill triggers, while `references/` is read only when the body names a "read this when…" condition. Only `officecli` uses it today.

Deployment mapping:

```
dotclaude/                      ~/.claude/
├── CLAUDE.md          ──────►  ├── CLAUDE.md       global charter, always loaded
├── settings.json      ──────►  ├── settings.json   permissions / model / cleanup
├── rules/             ──────►  ├── rules/          loaded on paths: glob match
├── skills/            ──────►  ├── skills/         description match or /<name>
│   └── synced/        ──╳───►  │                   (account-side backup, not deployed)
├── agents/            ──────►  └── agents/         only on subagent_type
├── 含中文翻譯/        ──╳───►  (not deployed, reference only)
└── .ref/              ──╳───►  (not deployed, superseded charters)
```

Deploy **only `rules/`, `skills/` (excluding `synced/`), `agents/`, and the three root files**. Keep `含中文翻譯/` out of `~/.claude/skills/` — placed there it collides with the real skills by name.

The placement rules live in section 1 of `rules/skill-authoring.md`. Read that table before adding anything: a repeatable multi-step procedure → a skill; a convention that applies every time a class of file is touched → a rule with `paths:`; a convention that applies only inside one task → a skill carrying `paths:`; build/test commands for one repo → that project's own CLAUDE.md; a one-off lesson that might generalise → `LESSONS.md`.

## Directory structure

```
dotclaude/
├── CLAUDE.md                    Global charter (10 sections). ★ User-maintained by hand; models never edit it, not even to append
├── CLAUDE.zh-TW.md              Chinese translation of the above, also user-maintained by hand
├── LESSONS.md                   Staging area for cross-project lessons; currently only a heading. The one file models may append to
├── settings.json                model=opus / effortLevel=high / git read-vs-write permission split
├── rules/
│   ├── markdown.md              **/*.md — no hard wrapping, blank line around blocks
│   ├── powershell.md            **/*.ps1 — three default encodings, syntax 5.1 lacks, native interop, verification list
│   └── skill-authoring.md       **/SKILL.md — full skill-writing spec and pre-ship checklist
├── skills/
│   ├── git-commit/              Conventional Commits 1.0.0 + house emoji prefix; prints commands, never runs them
│   ├── humanizer/               Strip AI-writing tells from English prose (Wikipedia-derived)
│   ├── humanizer-zh-tw/         Chinese counterpart; written in Chinese (the sole exception to the language rule)
│   ├── officecli/               .docx / .xlsx / .pptx via the officecli CLI
│   │   └── references/          elements / watch-marks / batch-raw, read only when the body says so
│   ├── python-plot/             matplotlib / seaborn figure conventions
│   ├── python-ui/               tkinter / ttkbootstrap desktop UI; used as a pair with ui-project
│   ├── readme/                  README.md required sections + language switcher and translation sync
│   ├── ui-project/              UI_README.html / 使用者指引.html / /design / PyInstaller packaging
│   └── synced/                  7 skills backed up from the claude.ai account; neither deployed nor maintained here
├── agents/
│   └── doc-verifier.md          Read-only documentation auditor subagent
├── 含中文翻譯/                  Mirror of the 15 English files above + 13 *.zh-TW.md translations
└── .ref/                        Superseded charters kept for reference (CLAUDE.Fable5.md / CLAUDE.RULES.md)
```

### Skill inventory

The norm for frontmatter here is **`name` and `description` and nothing else**. Two of the eight skills carry extra keys, each for a stated reason.

| Skill | Trigger | Extra frontmatter |
| --- | --- | --- |
| `git-commit` | Description match, or manual `/git-commit` | None |
| `humanizer` | Description match (editing English prose) | None |
| `humanizer-zh-tw` | Description match, or manual `/humanizer-zh-tw` | `argument-hint`, `context: fork`, `background: false`, `model: sonnet`, `effort: high` |
| `officecli` | Description match (Office files) | None; depends on the external `officecli` binary; ships `references/` |
| `python-plot` | Description match (drawing, saving, restyling a figure) | None |
| `python-ui` | `paths: **/*.py`, `**/*.spec` | `paths` |
| `readme` | Description match (writing or updating a README, adding a language) | None; preloaded by `doc-verifier` via `skills:` |
| `ui-project` | Description match (UI_README, 使用者指引, packaging) | None; preloaded by `doc-verifier` via `skills:` |

Three pairings:

- `readme` and `ui-project` used to be one skill. README rules apply to every project while UI_README.html and PyInstaller packaging apply only to App projects — binding two different trigger conditions together forced every README task to load the whole packaging ruleset, so they were split.
- `python-ui` is the lower layer and `ui-project` the upper one. The `.ico` and `sys._MEIPASS` rules live in `ui-project` alone; `python-ui` points at them instead of restating them, and opens by asking for both to be loaded together.
- `humanizer` handles English and `humanizer-zh-tw` handles Chinese; each description routes to the other so one request cannot half-trigger both.

`doc-verifier` is the only subagent here: `tools: Read, Grep, Glob, PowerShell` (no write tools), `skills: [readme, ui-project]`, `model: sonnet` / `effort: medium`. It reports problems and never edits files.

## Setup & run

No build, no test framework, no lint. "Deploying" means putting the files in the home directory:

```powershell
# First deployment (PowerShell) — excludes the translation mirror, the reference copies, and the account-side backup
Copy-Item -Path .\CLAUDE.md, .\settings.json, .\LESSONS.md -Destination "$env:USERPROFILE\.claude\" -Force
Copy-Item -Path .\rules, .\agents -Destination "$env:USERPROFILE\.claude\" -Recurse -Force
Copy-Item -Path .\skills -Destination "$env:USERPROFILE\.claude\" -Recurse -Force
Remove-Item "$env:USERPROFILE\.claude\skills\synced" -Recurse -Force -ErrorAction SilentlyContinue
```

**`settings.json` overwrites rather than merges.** Back up or diff the existing `permissions` block before copying over it.

### Verification

After changing any rule, these are the checks:

1. **Formatting** — per `rules/markdown.md`: one physical line per paragraph, one blank line around every block, a trailing newline, no BOM, no trailing whitespace.

2. **Mirror sync** — every English file under `含中文翻譯/` must be byte-identical to its top-level original:

   ```powershell
   $root = (Resolve-Path .).Path
   Get-ChildItem -Recurse -File -Filter *.md -Path .\含中文翻譯 |
     Where-Object { $_.Name -notlike '*.zh-TW.md' } |
     ForEach-Object {
       $orig = Join-Path $root $_.FullName.Substring((Join-Path $root '含中文翻譯').Length + 1)
       $ok = (Test-Path $orig) -and ((Get-FileHash $orig).Hash -eq (Get-FileHash $_.FullName).Hash)
       "{0,-6} {1}" -f $(if ($ok) { 'OK' } else { 'DRIFT' }), $_.Name
     }
   ```

3. **Section citations** — every `(global: X)` and `CLAUDE.md **X**` in these files must resolve to one of the 10 section names `CLAUDE.md` currently has. Renaming or deleting a section silently invalidates them.

4. **Frontmatter, key by key** — check each one by hand against the list in section 2 of `rules/skill-authoring.md`. A passing `claude plugin validate --strict` proves nothing here: it type-checks only `description`, `name`, `allowed-tools`, `metadata`, and `shell`, silently ignores every key it does not recognise, and never scans `rules/` at all.

5. **Actual triggering** — per section 8 of `rules/skill-authoring.md`, run 2–3 prompts phrased the way a request really arrives. A skill that fails to load is a `description` problem; a skill that loads but produces the wrong artifact is a body problem. The two repairs are different.

6. **Settings in effect** — run `/status`, `/model`, `/effort` in any project and check them against `settings.json`. When the product disagrees with this repo, trust the product and report the drift.

## Dependencies

- **Claude Code** (CLI / VS Code extension / Desktop) — the only runtime.
- **`officecli`** — needed by the `officecli` skill only; a single binary, no Office installation required. That skill checks `officecli --version` before doing anything and never installs it on its own initiative.
- Nothing else: no package manager, no runtime, no third-party libraries.

## Configuration

Current `settings.json` (user scope):

- `model: "opus"`, `effortLevel: "high"`, `cleanupPeriodDays: 21`
- `permissions.defaultMode: "auto"`
- `attribution.commit` / `attribution.pr` set to empty strings — no co-author trailers on commits or PRs
- `permissions.allow`: read-only git (`status` / `diff` / `log` / `show` / `branch --list`) runs without prompting
- `permissions.ask`: `add` / `commit` / `push` / `tag` / `merge` / `rebase` — all six force a confirmation prompt in every permission mode, matching the Git section of `CLAUDE.md`
- `theme: "dark"`, `autoUpdatesChannel: "latest"`, `agentPushNotifEnabled: true`

This repo contains no secrets and `settings.json` has no `env` block. If an API key is ever needed, put it in an environment variable, not here.

## Maintenance conventions

1. **`CLAUDE.md` is edited by the user, by hand, only** — models may not even append; propose changes in chat. The rule is stated on line 6 of the file itself.
2. **`LESSONS.md` is the one file models may append to**, and only for lessons that hold across projects, one per line as `- [YYYY-MM-DD] symptom → proposed global rule`. It is never loaded into a session, so appending changes no behaviour until the user promotes the lesson by hand. Over ~10 lines, say so.
3. **Skill, rule, and agent files need explicit approval in the session before an edit is applied.** Proposing a change is always fine; applying it unilaterally is not.
4. **Language rule**: conversation in Taiwanese Traditional Chinese; rule / skill / agent files in English. The sole exception is a file whose *subject* is a specific language (`humanizer-zh-tw`), which is written in the language it operates on.
5. **Omit `model:` / `effort:` by default** — omission is how a file inherits `settings.json`. An override must carry a written reason in the same file. The distinction that matters: on an inline skill the override changes the model for the **whole turn**, catching unrelated work in the same turn, while on a `context: fork` skill it applies to the fork alone. An override is therefore cheap on a forked skill and expensive on an inline one — prefer moving the skill to a fork over downgrading a turn.
6. **`background:` only does anything under `context: fork`.** On an inline skill it is inert and merely implies a behaviour that was never configured.
7. **When an English file changes, update both its copy under `含中文翻譯/` and the matching `.zh-TW.md` translation.** Translations render the body only; functional frontmatter keys such as `name` keep their original values. `humanizer` has no translation and `humanizer-zh-tw` needs none — those two gaps are deliberate, not oversights.
8. **Cite `CLAUDE.md` by section name, never by section number** — numbers drift as the file is edited.
