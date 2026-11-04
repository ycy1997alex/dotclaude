# CLAUDE.md

User-scope instructions (`~/.claude/CLAUDE.md`), loaded at the start of every session, in every project.
**Tradeoff:** these guidelines bias toward caution over speed. For trivial tasks, use judgment (§4 has the exemption).

**This file is modified ONLY by the user, manually. Models never edit it, including appending — propose changes in chat.**

## 0. Language & Environment

Unless the session specifies otherwise, always apply:

- Conversation replies: **臺灣繁體中文** (technical terms may stay in English)
- Code comments: 臺灣繁體中文, or English (when the term is a proper noun)
- Everything else in English: identifiers, file names, commit messages, rule and skill files.
- Exception: when a skill/agent/rule's SUBJECT is a specific natural language (e.g. `humanizer-zh-tw`, whose every pattern and example is 臺灣繁體中文), write that file in the language it operates on.
- Shell: use the PowerShell tool (Windows PowerShell 5.1), not the Bash tool (Git Bash), even where a harness hint suggests Bash. No bash-only syntax, no assuming bash behaviour. PowerShell 5.1 encoding pitfalls live in `~/.claude/rules/powershell.md` and load automatically when `.ps1` files are touched.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State your assumptions explicitly before implementing.
- If a simpler approach exists, say so before writing the complex one. Push back when warranted.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked. No "flexibility" or configurability nobody requested.
- No abstractions for single-use code. No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- Don't "improve" adjacent code, comments, or formatting. Don't refactor what isn't broken. Match existing style, even if you'd do it differently.
- Unrelated dead code: mention it, don't delete it. DO remove imports, variables, and functions that YOUR change orphaned.
- The test: every changed line traces directly to the user's request.
- Before risky or bulk edits: inside a git repo, ask the user to commit or stash first — never create `.bak` files in a repo, they pollute the tree and get committed by mistake. Outside git-managed directories, keep a `<name>.bak` beside the original.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

- In projects with a test suite:
  - "Fix the bug" → write a failing test that reproduces it, then make it pass.
  - "Add validation" → write tests for invalid inputs, then make them pass.
  - "Refactor X" → the same tests pass before AND after.
- Multi-step work: state the plan first, one line per step — `1. [step] → verify: [check]`.
- Strong criteria let you loop independently; weak criteria ("make it work") force constant clarification. "Done" means the check ran and passed, not "the code looks right."
- Exemption: single file, ≤ ~5 lines, no logic impact (typos, comments, formatting, doc text) — verify by inspecting or running the result instead of writing a test.

## 5. Stop and Ask the User When

- Data would be deleted or overwritten with no backup path.
- Two instructions conflict — e.g. §3 Surgical Changes vs. a request that requires touching 30 files. Confirm scope first.
- Acceptance criteria can't be made concrete ("make it better") → ask for one measurable target. "Make the tests pass" is already concrete; proceed.
- The same approach failed twice. A third attempt is the wrong approach, not insufficient effort.
- Taste calls with no technical winner (naming, UX wording, tradeoffs) → present options with tradeoffs; don't decide alone.
- Asking the user to choose a threshold or selection rule → show each candidate with its false-positive rate measured on a placebo or shuffled null and the counts it yields, never the abstract rule alone (procedure: the `null-calibration` skill).

## 6. Security & Environment

- Never hardcode or commit secrets. Keys live in environment variables or untracked config; confirm `.gitignore` covers them before the first commit.
- Logs, error messages, exports, and debug output must never contain PII/PHI. Use anonymised IDs or masked values.
- Remove or gate debug prints (logging level / debug flag) before declaring a deliverable done.
- Windows filesystems are case-insensitive: writing to `NewCase.ext` overwrites an existing `oldcase.ext`, and deleting the "old" name then destroys the new content. To change only the case of a filename, `mv` to a temporary name and then `mv` to the target — never "write new file + delete old file".
- Confirm the active conda/venv environment and switch to the intended one before installing or running anything; never install into `base` by assumption.
- The first time a project's build/test/lint/run commands are worked out, record them in that project's own CLAUDE.md.

## 7. Delegation to Subagents

**Delegate for context isolation, not by default.** Subagents run in the background by default; their result arrives as a later notification.

- Delegate when the subtask would dump bulk into the main context: scanning many files, long logs or web pages, full test suites, bulk edits.
- When the side task needs THIS conversation's accumulated context, prefer a fork (`/subtask`): it inherits the full history and shares the prompt cache, so it's cheaper than a fresh subagent. Use a named subagent when the task needs isolation or tool limits instead.
- The built-in Explore and Plan agents do NOT load CLAUDE.md or git status — restate any critical constraint in the delegation prompt.
- Every delegation states three things: the goal and why it matters; concrete acceptance criteria (tests pass / file contains sections X and Y / grep returns zero matches); and the report format — conclusions plus `file:line` only, long output written to a file with the path returned.
- **Verification is never self-verification.** Files: read them back yourself. Code: run it. High-risk judgment: a second opinion from a fresh-context agent.

## 8. Git

- **Never run `git add`, `git commit`, `git push`, `git tag`, `git merge`, or `git rebase` on your own initiative** — not when the task is finished, not when the diff looks clean, not as the last step of a plan you proposed. Committing is user-initiated, always.
- All six operations trigger a mandatory confirmation prompt (`permissions.ask` in settings) in every permission mode. Expect the prompt; never work around it.
- When a commit looks warranted, say so in one line and stop. Running the `/git-commit` skill is allowed and expected: it writes the message and shows the user the exact `add` → `push` commands under its conventions. Showing the commands is the deliverable; running them is the user's.
- Read-only git (`status`, `diff`, `log`, `show`, `branch --list`) is allow-listed and fine at any time.

## 9. Memory & Maintenance

- **Auto memory** (on by default, `~/.claude/projects/<project>/memory/`) is where project-scoped learnings live — maintain it as you work; the user audits it via `/memory`. Do not duplicate project-scoped lessons anywhere else.
- **`LESSONS.md`** (beside this file) is the one file here models may append to, and ONLY for lessons that would hold across projects — candidates for promotion into this file, a skill, or a rule. When a project lesson turns out to generalise, propose it here. One line per lesson: `- [YYYY-MM-DD] symptom → proposed global rule`. Create it if missing. It is never loaded into any session — appending changes no behaviour until the user promotes the lesson. Over ~10 lines, tell the user.
- Skill, rule, and agent files (`~/.claude/skills/*/SKILL.md`, `~/.claude/rules/<topic>.md`, `~/.claude/agents/*.md`): models may propose edits, but apply them only with the user's explicit approval in that session.
