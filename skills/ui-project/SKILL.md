---
name: ui-project
description: >-
  Rules for App-project documentation and packaging: UI_README.html developer architecture doc, 使用者指引.html end-user manual, cross-document sync, and PyInstaller .spec packaging (onefile/onedir, sys._MEIPASS resource paths, icons). Apply to any task that writes or updates UI_README.html / 使用者指引.html, or does PyInstaller packaging. README.md and its translations are covered by the separate `readme` skill.
model: opus
effort: medium
---

# Software Documentation & Packaging Rules

Scope: §2–§3 and §5 apply only to App projects (runnable application with a user interface); §4 applies whenever more than one document in the set exists. Record per-project decisions ("include UI_README.html?", "使用者指引 needed?", "onefile or onedir?") in that project's own CLAUDE.md so later sessions don't re-ask.

## 1. README.md — see the `readme` skill

Every project needs a `README.md` at the repo root, and it is the one document in this set that is never optional. Its required sections, audience, language, and multi-language conventions (translation filenames, the switcher line under the H1) live in the `readme` skill — load that skill when writing or updating a README instead of duplicating the rules here.

The rest of this file assumes that README exists, and §4 keeps it in sync with the documents below.

## 2. UI_README.html — developer architecture doc (App projects, opt-in)

When the app first becomes runnable, ASK the user whether this project should include it; record the answer in the project's CLAUDE.md. If yes: a single self-contained HTML file (inline CSS/JS, no CDN, opens by double-click). Language: 台灣繁體中文，專有名詞用英文.

Focus: **code flow and architecture design** — module design and interaction relationships, plus features and limitations. This is an architecture document, NOT a code walkthrough.

Required content:

- **Project overview & module design**: what the app is, each module's responsibility and boundary.
- **Module interaction map**: how modules depend on and call each other; one diagram (Mermaid / inline SVG / ASCII) of the dependency and data flow.
- **Screen/component map**: every window, page, or major widget → the source file and class/function implementing it (reference by name only).
- **Interaction flow**: per feature, user action → event handler → model/service call → UI update, described at the function-name level.
- **State management**: where state lives, how it propagates.
- **Features & limitations**: what the app can do, known constraints, what it is NOT designed for.
- Must be interactive (collapsible sections / navigation sidebar / tabs), not just scrollable text.

Prohibited: pasting function bodies or explaining code line-by-line. Reference code by symbol name or `file:line` instead.

## 3. 使用者指引.html — end-user manual (on release only)

Create only when the app will be packaged and delivered to non-developers; if delivery plans are unclear, ask. Audience: non-technical end users. Language: 台灣繁體中文, plain everyday wording over jargon. A single self-contained HTML file.

**Standalone constraint (hard rule)**: assume the end user receives EXACTLY two files — the `.exe` and `使用者指引.html`. Therefore:

- Content covers ONLY (a) how to operate the .exe, and (b) how to read and interpret everything the app produces on screen or as output files.
- Never mention README.md, UI_README.html, source files, code, file paths, development tools, or any development context.
- Stamp the app version and date the guide corresponds to.

Required sections:

- **快速開始**: launch the .exe and complete the single most common task, step by step.
- **畫面導覽**: each screen/panel, with annotated screenshots or inline-SVG mockups (no external image files).
- **結果解讀**: how to read every output — what the numbers mean, what ranges are normal, what actions they suggest; how to open/interpret any files the app produces.
- **使用建議與限制**: usage tips, known limitations, what the app is NOT for.
- **常見問題與疑難排解**: FAQ + error messages the user may see and what to do.

## 4. Sync rule — touch one, check all

- When ANY document in this set changes — or a code change alters what any of them describes — check ALL existing documents in the set (README.md, README.en.md if present, UI_README.html, 使用者指引.html) and update every affected one in the SAME commit. Stale docs = failing acceptance check (global: Goal-Driven Execution).
- When a doc update would be large, list the affected sections and confirm scope with the user first (global: Stop and Ask).
- Verification (global: Goal-Driven Execution): after writing or updating a doc, read it back and confirm all required sections exist. "File written" is not "done."

## 5. PyInstaller packaging (.spec)

- **Default: onefile.** Switch to onedir ONLY when the onefile output is too large or startup is unacceptably slow — state the measured reason (size / launch time) and record the decision in the project's CLAUDE.md.
  - Exception: when packaging or measuring is expected to take a long time (e.g., heavy dependencies like torch/tensorflow, large bundled data/models), do NOT run the build just to measure — warn the user first, state the estimated reason (dependency footprint, expected build time), and let the user decide onefile vs onedir before packaging. Record the decision and its basis ("estimated, not measured") in the project's CLAUDE.md.
- Runtime resources (icons, data files, models): access through a `sys._MEIPASS`-aware path helper; onefile extracts to a temp dir, so hardcoded relative paths break.
- App icon: set `icon=` in the .spec; the .ico must be multi-resolution (at minimum 16, 32, 48, 256 px) — verify before packaging, a single-size .ico renders blurry or falls back to a default icon.
- After packaging, smoke-test the actual .exe: launch it and run the single most common task. "Built" is not "done" (global: Goal-Driven Execution).
- If 使用者指引.html exists, confirm its version/date stamp matches this build (§4 sync rule).
