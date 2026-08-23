---
name: git-commit
description: >-
  Write commit messages in Conventional Commits 1.0.0 with the house emoji prefix, and apply the repository conventions for staging, branching, tagging, merging, reverting, and editing history. Invoked manually via /git-commit; the model never starts a git write operation on its own (global: Git).
disable-model-invocation: true
model: sonnet
effort: medium
---

# Git Commit Rules

Base spec: **Conventional Commits 1.0.0**. Everything below is the spec itself unless marked **[house]** — those are local extensions or restrictions that go beyond it. Keep the distinction: when a tool disagrees with this file, the spec wins on unmarked rules and this file wins on marked ones.

## 1. Message format

```
<emoji> <type>[(scope)][!]: <description>

[body]

[footer(s)]
```

### Header

- **emoji [house]** — exactly one, taken from the table in §2, always first, followed by a single space. This sits *outside* the spec's grammar: a strict parser expects the message to begin with `type`. If commitlint or a CI check is ever added, configure a custom `headerPattern` rather than dropping the emoji.
- **type** — a noun, lowercase, exactly one. `feat` MUST be used when the commit adds a feature; `fix` MUST be used when it patches a bug. The spec allows arbitrary additional types; **[house]** the table in §2 is a closed set.
- **scope** — optional but preferred. A noun in parentheses naming the section of the codebase: `plot`, `io`, `gui`, `docs`. Omit only when the change is genuinely repo-wide.
- **`!`** — placed after type/scope, immediately before the colon, to flag a breaking change. See §4.
- **`: `** — colon plus exactly one space, then the description.
- **description** — imperative mood ("add", not "added"/"adds"), lowercase start, no trailing period.
- **[house]** Header ≤ 72 characters including the emoji. The emoji is one code point but two terminal columns, so `git log --oneline` truncates slightly earlier than the count suggests.

### Body

- Optional; separated from the header by one blank line. Free-form, may span multiple paragraphs. Wrap at 72 characters — this applies to the commit message only.
- Explains WHAT changed and WHY — never how; the diff already says how.
- **[house]** Required when the change is not self-evident from the diff, and always required for initial commits (§3) and breaking changes (§4).

### Footers

- One or more, after a blank line following the body. Each is `Token: value` or `Token #value`.
- A token uses `-` in place of spaces: `Reviewed-by`, `Refs`. The one exception is `BREAKING CHANGE`, written with a space and in uppercase.
- `BREAKING-CHANGE` is a valid synonym for `BREAKING CHANGE`. **[house]** Prefer the spaced uppercase form.
- Issue references use `Refs: #123` (comma-separated for several).
- **[house]** No AI attribution trailers. `attribution` is cleared in settings; never hand-write `Co-Authored-By: Claude` or "Generated with Claude Code".

### Commit scope

- **[house]** One logical change per commit. Never mix refactoring with a behaviour change, or formatting with logic.

## 2. Type → emoji (fixed mapping; exactly one emoji, always first)

| type | emoji | use for |
|---|---|---|
| feat | ✨ | new feature or capability |
| fix | 🐛 | bug fix |
| docs | 📝 | documentation only (incl. README / UI_README / 使用者指引) |
| style | 🎨 | formatting, whitespace, naming — zero logic change |
| refactor | ♻️ | code restructuring — zero behaviour change |
| perf | ⚡️ | performance improvement |
| test | ✅ | add or fix tests |
| build | 📦️ | build system, packaging (`.spec`), dependencies |
| ci | 👷 | CI configuration |
| chore | 🔧 | maintenance or tooling not covered above |
| revert | ⏪️ | revert a previous commit (see §5) |

Examples:

```
✨ feat(plot): add dynamic 5% y-axis padding helper
```

```
📝 docs(readme): sync setup commands after conda env rename
```

## 3. Initial commit — the one exception to the fixed mapping

A repository's first commit uses 🎉. It is the only emoji outside the table in §2, and the only commit whose emoji is chosen by occasion rather than by type.

- Empty scaffold, no working feature yet:

  ```
  🎉 chore: initial commit
  ```

- `git init` over an already-working codebase — keep 🎉, pick the type by what the commit actually contains:

  ```
  🎉 feat: initial commit
  ```

- No scope: the initial commit is repo-wide by definition.
- Body is mandatory here — state what the repository is for and what this first commit contains. This is never self-evident from a diff that is 100% additions.
- Before the initial commit, verify `.gitignore` covers secrets, virtual envs, and generated artifacts (global: Security & Environment). A secret committed here can only be removed by rewriting history, which §7 forbids.

## 4. Breaking changes

The spec accepts *either* `!` in the header *or* a `BREAKING CHANGE:` footer. **[house] require both** — `!` alone is easy to miss in `git log --oneline`, and the footer is what a reader (or a changelog generator) actually reads.

- `!` may follow any type, not only `feat` and `fix`.
- The footer states what breaks and what the caller must do instead.

```
🐛 fix(io)!: reject NIR frames with missing wavelength header

The loader silently zero-padded absent wavelength columns, which
produced plausible-looking but wrong feature vectors downstream.

BREAKING CHANGE: loader now raises ValueError instead of zero-padding.
Callers relying on the old behaviour must pad explicitly before loading.
```

## 5. Revert

The spec leaves revert handling to implementers; this is the house shape:

```
⏪️ revert: <description of the commit being reverted>

This reverts commit <full-hash>.

Refs: <full-hash>
```

Reverting several commits: list every hash in `Refs`, newest first.

## 6. Branches and tags

- **Branch**: `<type>/<short-kebab-description>`, using a type from §2 — `feat/ceg-bias-export`, `fix/ico-taskbar-icon`.
- **Tag**: SemVer with a `v` prefix (`v1.2.3`). Always annotated (`git tag -a`), never lightweight; the tag message is the release summary.
- **Merge**: `--no-ff` into a long-lived branch, so the branch topology and the grouping of commits survive in history.

## 7. Workflow guardrails

- **Never initiate.** `commit` / `push` / `tag` / `merge` / `rebase` are always started by the user (global: Git) — not on task completion, not on a clean diff, not as a plan's final step. When work reaches a commit point, say so in one line and stop.
- All five raise a `permissions.ask` confirmation. Expect it; never work around it.
- Before staging: run `git status` and `git diff --staged`. Stage explicitly by path. Never `git add -A` or `git add .` while the tree holds unrelated changes.
- Never `git push` unless explicitly asked. Never force-push. Never rewrite history that has been pushed.
- `git commit --amend` only on commits that have not been pushed.
- A failing pre-commit hook is reported and fixed, never bypassed with `--no-verify`.
- Backups inside a repo use commit or stash, never `.bak` copies (global: Surgical Changes).
- Never commit: secrets (global: Security & Environment), `.bak` files, virtual environments, large generated artifacts (packaged `.exe`, model weights), or data containing PII/PHI. Check `.gitignore` covers them first; propose additions if it doesn't.

## 8. When unsure

- Working tree holds multiple unrelated changes → propose a split into separate commits; ask if the grouping isn't obvious.
- The right `type` is ambiguous (e.g. a refactor that also fixes a bug) → split it. If it genuinely can't be split, choose by primary intent and say so in the body.
- Unclear whether a change is breaking → treat it as breaking. A spurious `!` costs a reader ten seconds; a missing one costs a caller a debugging session.
- A merge conflict touches code outside the current task's scope → stop and ask (global: Stop and Ask).