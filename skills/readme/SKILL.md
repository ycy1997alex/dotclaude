---
name: readme
description: >-
  Rules for a project's README.md — required sections (Overview, Architecture, Directory structure, Setup & run, Dependencies, Configuration), audience and language, and the multi-language convention (translation filenames, the "繁體中文 | English" switcher line under the H1, sync between versions). Apply to any task that creates, rewrites, or updates README.md, README.en.md, or any other README translation, including adding a second language to an existing README or being asked how a language switcher should be written.
---

# README Rules

Every project has a `README.md` at the repo root — it is both the repo's front page and the developer summary. §1 applies to every project; §2 applies only once a second language is involved.

## 1. Required sections

Audience: developers and repo visitors. Language: Taiwan Traditional Chinese (臺灣繁體中文); technical terms may stay in English.

- **Overview**: what the project does, 3–5 sentences.
- **Architecture**: pattern used, module responsibilities, one ASCII/Mermaid data-flow diagram.
- **Directory structure**: annotated tree of key files/folders.
- **Setup & run**: exact commands — install dependencies, dev run, build/package, platform notes.
- **Dependencies**: key libraries, one line each on why chosen.
- **Configuration**: config files, environment variables, where API keys live (never commit secrets — global: Security & Environment).

Skip a section only when it is genuinely inapplicable — a one-file script has no Architecture, a config-only repo has no Dependencies. Drop the heading entirely rather than padding it with filler; an empty section costs the reader more than a missing one.

## 2. Multi-language READMEs

A translation is optional. Create one only when the user asks, or when the repo is public-facing.

### Filenames

Name translations `README.<BCP 47 tag>.md` beside the root `README.md`, language subtag lowercase and region subtag uppercase: `README.en.md`, `README.zh-TW.md`, `README.ja.md`, `README.pt-BR.md`. Avoid `README_EN.md` and `README.En.md`.

When the repo already suffixes other translated files a particular way (`CLAUDE.zh-TW.md`, `markdown.zh-TW.md`), follow that — internal consistency wins over the external convention when the two disagree.

### Switcher line

Put one plain-text line directly under the H1, blank line above and below. The current language is unlinked; every other language is a link.

`README.md`:

```markdown
# project-name

繁體中文 | [English](README.en.md)
```

`README.en.md`:

```markdown
# project-name

[繁體中文](README.md) | English
```

Three or more languages extend the same line: `繁體中文 | [English](README.en.md) | [日本語](README.ja.md)`.

Leaving the current language unlinked is the whole mechanism — a link pointing at the page the reader is already on does nothing except hide which version they landed on. Do not use shields.io badges or `<div align="center">`; those belong to outward-facing marketing repos and render inconsistently across GitHub, editors, and plain markdown viewers.

The H1 stays identical in every version — it is the repo name, not a translated title.

### Sync

Every language version carries the same sections, in the same order, saying the same thing. When one changes, update all of them in the same commit; a stale translation is worse than no translation, because it is trusted.

Paths and filenames inside links are case-sensitive on GitHub. A switcher pointing at `README.En.md` when the file is `README.en.md` is a broken link that renders fine locally on Windows.

## 3. Verification

After writing or updating any README (global: Goal-Driven Execution):

1. Read the file back and confirm every required section from §1 is present, or deliberately inapplicable.
2. If translations exist, confirm each one's switcher line names every language, links all of them except its own, and that each linked filename exists with exactly that casing.
3. Confirm no secret, key, or real hostname appears in any example command.
