---
name: git-commit
description: >-
  Writes a Conventional Commits 1.0.0 message with the house emoji prefix, then prints the exact `git add` → `git commit` → `git push` sequence for the user to run. Load this whenever work reaches a commit point, or the user says "commit", "幫我 commit", "寫 commit message", "commit 訊息怎麼寫", "要 push 了", "存一版", or asks how a change should be worded. Composing and printing the commands is this skill's output; the user runs them (global: Git).
---

# Git Commit Rules

Base spec: **Conventional Commits 1.0.0**. Everything below is the spec itself unless marked **[house]** — those are local extensions or restrictions that go beyond it. Keep the distinction: when a tool disagrees with this file, the spec wins on unmarked rules and this file wins on marked ones.

**[house] Header only.** Write the header line and stop. The spec makes body and footers optional (rule 6: "A longer commit body MAY be provided"); this repo never writes one, with the two narrow exceptions in §4 and §5. A change that needs a paragraph of explanation is usually two commits.

## 1. Message format

```
<emoji> <type>[(scope)][!]: <description>
```

- **emoji [house]** — exactly one, taken from the table in §2, always first, followed by a single space. This sits *outside* the spec's grammar: a strict parser expects the message to begin with `type`. If commitlint or a CI check is ever added, configure a custom `headerPattern` rather than dropping the emoji.
- **type** — a noun, lowercase, exactly one. `feat` MUST be used when the commit adds a feature; `fix` MUST be used when it patches a bug. The spec allows arbitrary additional types; **[house]** the table in §2 is a closed set.
- **scope** — optional but preferred. A noun in parentheses naming the section of the codebase: `plot`, `io`, `gui`, `docs`. Omit only when the change is genuinely repo-wide.
- **`!`** — placed after type/scope, immediately before the colon, to flag a breaking change. See §4.
- **`: `** — colon plus exactly one space, then the description.
- **description** — imperative mood ("add", not "added"/"adds"), lowercase start, no trailing period.
- **[house]** Header ≤ 72 characters including the emoji and the space after it. Terminals render most of these emoji two columns wide, so `git log --oneline` looks slightly wider than the character count suggests.

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

The eleven types are the spec's `feat` and `fix` plus the eight it recommends (`build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`) and `revert`. The emoji follow the gitmoji convention, so a reader who knows gitmoji reads them without a legend.

Examples:

```
✨ feat(plot): add dynamic 5% y-axis padding helper
```

```
📝 docs(readme): sync setup commands after conda env rename
```

```
🔧 chore(deps): pin ttkbootstrap to 1.10.1
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
- Before the initial commit, verify `.gitignore` covers secrets, virtual envs, and generated artifacts (global: Security & Environment). Removing a secret from the first commit means rewriting history — cheap while nothing has been pushed, and forbidden once it has (§8).

## 4. Breaking changes

The spec accepts *either* `!` in the header *or* a `BREAKING CHANGE:` footer. **[house] use `!` in the header.** It is the short form, and it is what shows up in `git log --oneline`.

- `!` may follow any type, not only `feat` and `fix`.
- The description after the colon says what broke, in the imperative: `🐛 fix(io)!: raise on NIR frames with a missing wavelength header`.
- Add a single `BREAKING CHANGE:` footer **only** when the caller has to do something the header cannot fit — one line, after a blank line:

  ```
  🐛 fix(io)!: raise on NIR frames with a missing wavelength header

  BREAKING CHANGE: callers relying on zero-padding must pad explicitly before loading.
  ```

## 5. Revert

The spec leaves revert handling to implementers; this is the house shape. The hash is the one piece of information that cannot go in the description, so a revert carries a single `Refs:` footer:

```
⏪️ revert: add dynamic 5% y-axis padding helper

Refs: 4f2a9c1
```

Reverting several commits: list every hash in `Refs`, newest first, comma-separated.

## 6. Branches and tags

- **Branch**: `<type>/<short-kebab-description>`, using a type from §2 — `feat/ceg-bias-export`, `fix/ico-taskbar-icon`.
- **Tag**: SemVer with a `v` prefix (`v1.2.3`). Always annotated (`git tag -a`), never lightweight; the tag message is the release summary.
- **Merge**: `--no-ff` into a long-lived branch, so the branch topology and the grouping of commits survive in history.

## 7. Output — the command sequence

**The commands are the deliverable, not their execution.** Inspect the tree, compose the message, print a copy-pasteable block, and stop. Never run `add`, `commit`, or `push` (§8).

Inspect first — `git status` and `git diff` are allow-listed, so run them to decide what belongs in the commit:

```powershell
git status
git diff
```

Then print the sequence. Stage explicitly by path — never `git add -A` or `git add .` while the tree holds unrelated changes:

```powershell
git add skills/python-plot/SKILL.md skills/python-ui/SKILL.md
git commit -m "📝 docs(skills): document the verification step for plot and UI rules"
git push
```

- Emoji survive PowerShell 5.1 arguments intact (they are passed as UTF-16), so `-m "✨ feat: ..."` is safe on Windows. Do **not** pipe the message into `git commit -F -` — piped bytes go through `$OutputEncoding`, which defaults to ASCII and turns every emoji into `?`.
- **Include `git push` only when the user has asked to push.** Otherwise the block ends at `commit`, with one line saying the branch is ready to push.
- The working tree holds several unrelated changes → print one `add` + `commit` pair per logical commit, in the order they should be run, and say why they are split.

## 8. Workflow guardrails

- **Never initiate.** `add` / `commit` / `push` / `tag` / `merge` / `rebase` are always started by the user (global: Git) — not on task completion, not on a clean diff, not as a plan's final step. When work reaches a commit point, say so in one line and print the block from §7.
- All six raise a `permissions.ask` confirmation. Expect it; never work around it.
- **[house]** One logical change per commit. Never mix refactoring with a behaviour change, or formatting with logic.
- **[house]** No AI attribution trailers. `attribution` is cleared in settings; never hand-write `Co-Authored-By: Claude` or "Generated with Claude Code".
- Never force-push. Never rewrite history that has been pushed.
- `git commit --amend` only on commits that have not been pushed.
- A failing pre-commit hook is reported and fixed, never bypassed with `--no-verify`.
- Backups inside a repo use commit or stash, never `.bak` copies (global: Surgical Changes).
- Never commit: secrets (global: Security & Environment), `.bak` files, virtual environments, large generated artifacts (packaged `.exe`, model weights), or data containing PII/PHI. Check `.gitignore` covers them first; propose additions if it doesn't.

## 9. When unsure

- Working tree holds multiple unrelated changes → propose a split into separate commits; ask if the grouping isn't obvious.
- The right `type` is ambiguous (e.g. a refactor that also fixes a bug) → split it. If it genuinely can't be split, choose by primary intent and say so when printing the block.
- Unclear whether a change is breaking → treat it as breaking. A spurious `!` costs a reader ten seconds; a missing one costs a caller a debugging session.
- A merge conflict touches code outside the current task's scope → stop and ask (global: Stop and Ask the User When).

## 10. Verification

Before printing the block, check the message against this list (global: Goal-Driven Execution):

1. Exactly one emoji, first, from §2 — or 🎉 for an initial commit.
2. The type is one of the eleven in §2, lowercase, followed by an optional `(scope)`, an optional `!`, then `: ` with exactly one space.
3. Description is imperative, lowercase start, no trailing period.
4. Header ≤ 72 characters.
5. No body. A footer appears only in the two cases of §4 and §5, and is one line.
6. Every path in `git add` appears in `git status`, and nothing in the block stages a file the user did not ask to commit.
7. `git push` appears only if the user asked to push.

A message that fails any line is rewritten before it is shown, not shown with a caveat.
