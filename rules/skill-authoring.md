---
name: skill-authoring
description: Conventions for writing, reviewing, and editing SKILL.md files and their bundled resources.
paths:
  - "**/SKILL.md"
  - "**/.claude/skills/**"
---

# Authoring SKILL.md

These conventions load automatically whenever a SKILL.md or anything under a `skills/` directory is touched. They apply to the skill being written — not to this file.

A skill packages a *procedure* so it can be loaded on demand instead of living permanently in CLAUDE.md. Everything below assumes the global CLAUDE.md is already loaded; a skill extends it and never repeats it.

---

## 1. Decide whether it should be a skill

Use the attribution rule from CLAUDE.md **Memory & Maintenance** before writing anything:

| Content | Destination |
| --- | --- |
| A repeatable multi-step procedure | `skills/<name>/SKILL.md` |
| A convention that applies every time a class of file is touched | `rules/<topic>.md` with `paths:` (this file, `rules/powershell.md`) |
| A convention that applies only inside one task | a skill carrying `paths:` |
| Build / test / lint / run commands for one repo | that project's own CLAUDE.md |
| A one-off lesson that may become a global rule | `LESSONS.md` |

If the guidance already exists in the global CLAUDE.md, do not restate it. Point at it by **section name**, never by section number — numbers drift when the file is edited.

Stop and ask before creating a skill that overlaps an existing one. Two skills covering the same ground is worse than one longer skill: both will half-trigger.

---

## 2. Frontmatter

Required:

- **`name`** — kebab-case, identical to the containing directory name.
- **`description`** — one paragraph, third person, stating **what the skill does** *and* **when it should trigger**. This is the only thing the model sees before deciding to load the skill, so all "when to use" information belongs here and nowhere else.

Optional, and omitted by default:

- **`paths:`** — glob list, for skills that only apply to a file class.
- **`model:` / `effort:`** — omit to inherit the session settings, which are the ones in `settings.json` (`model`, `effortLevel`). Set one only as a deliberate override, and state the reason in a short `## Why this overrides the session model` section in the same file. `effort:` has no `inherit` value — omitting the field *is* inheritance. **On an inline skill the override changes the model for the whole turn**, including the unrelated work either side of the skill's own steps; on a `context: fork` skill it applies to the fork alone. So an override is cheap on a forked skill and expensive on an inline one — prefer moving the skill to a fork over downgrading a turn. Never set a value that merely restates the session default; it changes nothing and still has to be read.
- **`context: fork`** — only when the skill needs an isolated context. Without it the skill runs inline: it sees the conversation history, and any `model:` / `effort:` override lands on the whole turn. A forked skill sees none of that history, so everything it works on must arrive as an argument or a file path — say so in the body, and give the skill an `argument-hint:`.
- **`background:`** — meaningful **only** together with `context: fork`; on an inline skill it is inert and merely implies a behaviour that was never configured. `false` keeps the caller waiting and delivers the result into the conversation; `true` runs the fork in the background and reports back as a task notification. Set it explicitly on every forking skill rather than leaving the choice to the default.
- **`allowed-tools:`** — only when the skill would otherwise be tempted to reach for tools it should not use.

### Writing the description

The common failure is **under**-triggering, not over-triggering. Write the description so the trigger conditions are explicit and slightly insistent.

**Weak:** `Helps with plotting.`

**Strong:** `Applies the project's Matplotlib/seaborn figure conventions — GridSpec layout, dpi=300, tight bounding box, dynamic y-axis padding. Use this whenever a plot, chart, or figure is being produced or restyled in Python, including quick one-off diagnostic plots and any call to plt.subplots, sns.lineplot, or savefig.

Name the concrete surface forms a request will take (file extensions, tool names, the words a person actually types), not an abstract category.

---

## 3. Language

Per CLAUDE.md **Language & Environment**: skill files are written in **English** — body, headings, identifiers, filenames, and examples.

The single exception is a skill whose subject *is* a specific language (for example a zh-TW writing skill); write that one in the language it teaches, because its examples are the content.

---

## 4. Structure and progressive disclosure

```
skill-name/
├── SKILL.md          # required — frontmatter + procedure
├── references/       # loaded only when SKILL.md points at them
├── scripts/          # executed, not read into context
└── assets/           # templates, icons, fonts used in output
```

Three loading levels: metadata is always in context, the SKILL.md body loads when the skill triggers, bundled files load only when the body says to read them. Design for that budget:

- Keep the body under ~500 lines. Approaching the limit means the content wants another layer — move detail into `references/` and leave a one-line pointer saying *when* to open it.
- Give any reference file over ~300 lines a table of contents.
- When a skill covers several variants of the same workflow, split by variant (`references/aws.md`, `references/gcp.md`) so only the relevant one is read.
- Put deterministic, repetitive work in `scripts/` rather than describing it in prose. A script that runs is cheaper and more reliable than instructions that must be re-derived every time.

---

## 5. Writing style

- **Imperative.** "Rasterize the page before comparing" beats "the page should be rasterized".
- **Explain the reason, once.** A rule with a stated cost is followed under pressure; a bare `MUST` is followed until it becomes inconvenient. Reserve emphatic phrasing for the two or three places where a mistake is expensive.
- **Generalize past the example that prompted the skill.** Examples illustrate; they are not the specification.
- **Define the output shape explicitly** when the skill produces an artifact — an exact template block is worth more than a paragraph describing one.
- **End with verification.** Per CLAUDE.md **Goal-Driven Execution**, a procedure is not finished until a stated check has been run and passed. Every procedural skill names its own success condition.

---

## 6. Constraints a skill inherits and must not violate

- **Git** — a skill never instructs `commit`, `push`, `tag`, `merge`, or `rebase`, not as a final step, not as cleanup. It may prepare a commit message and stop there.
- **Security** — no real keys, hostnames, patient identifiers, or PII/PHI anywhere in a skill, including example output. Use obviously fake placeholders.
- **Simplicity** — do not add configuration knobs, fallbacks, or error handling for situations the skill's own procedure cannot reach.
- **Surgical Changes** — skills that edit code inherit this by default; only restate it where the procedure would otherwise invite a broad rewrite.
- **Self-modification** — a skill file may be *proposed* for change at any time, but is edited only with explicit approval in that session.
- **Safety** — a skill's behaviour must match what its description says it does. No skill that hides its effect, exfiltrates data, or bypasses a permission prompt.

---

## 7. Pre-ship checklist

1. `name` matches the directory; `description` states both what and when.
2. `model:` / `effort:` are absent, or present with a written reason.
3. Body is English, imperative, under ~500 lines.
4. No content duplicated from CLAUDE.md; references use section names, not numbers.
5. No git write operations, no secrets, no PII/PHI.
6. Every reference file is pointed at from the body with a "read this when…" condition.
7. The procedure ends in a verifiable check.
8. Every frontmatter key is checked by hand against the §2 list. `claude plugin validate --strict` passing proves nothing here: it type-checks only `description`, `name`, `allowed-tools`, `metadata`, and `shell`, silently ignores every key it does not recognise, and never scans `rules/` at all. A misspelled or misplaced key sits there looking configured and does nothing.

---

## 8. Test before adopting

Write 2–3 prompts phrased the way a request would actually arrive — not the description read back to the model. Run them with the skill available and check two separate things:

- **Triggering** — did the skill load at all? If not, the description is the problem, not the body.
- **Output** — did following the body produce the intended artifact? If a step had to be improvised, that step is missing from the skill.

Revise and rerun. Fixing the description and fixing the body are different repairs; do not confuse a triggering failure for a content failure.

---

## 9. Skeleton

```markdown
---
name: <kebab-case-name>
description: <what it does> + <when to trigger, in concrete surface terms>
---

# <Title>

<One or two sentences: the situation this skill exists for.>

## Procedure

1. <step> → verify: <check>
2. <step> → verify: <check>

## Output format

<Exact template, if the skill produces an artifact.>

## References

- `references/<topic>.md` — read when <condition>.
```
