---
name: handoff
description: >-
  Writes a handoff letter to the next session: what this session left unfinished, the 3–5 things about this environment the user never asked about but that matter most, and the most likely way this setup will degrade plus how to prevent it. Runs only when the user types /handoff, typically right before closing a long session or switching to a fresh one.
disable-model-invocation: true
---

# Handoff letter

The user runs `/handoff` when this session's work has to continue in a new one. The next session sees nothing of this conversation, so the letter must stand on its own: every item names the file, command, or decision it is about.

Write only from what this session actually saw — files read, command output, failures, the user's own decisions. A point with no evidence behind it is a guess and stays out.

## Procedure

1. List the unfinished items: work requested but not done, steps skipped, checks that failed or never ran, and decisions still waiting on the user. Give each its current state and the next concrete step. → verify: no item says only "continue" or "finish up"; each names a path, command, or question.
2. Pick 3–5 things about this environment that the user never asked about but that you judge most important for working in it — gotchas hit, conventions inferred, fragile spots noticed. → verify: each cites where in this session it was seen.
3. Name the single most likely way this setup will degrade over the coming sessions, and the action that prevents it. → verify: the prevention is something the user or the next session can actually do, not "be careful".
4. Output the letter in the template below, in the reply language from CLAUDE.md **Language & Environment**, inside one fenced block so it can be pasted into the next session as-is. Then stop — start or resume no other work in the same turn.

## Output format

```markdown
# Letter to the next session (YYYY-MM-DD)

## Unfinished
1. <item> — state: <where it stands>. Next: <concrete step>.

## Things I was never asked about, but matter most
1. <point> — seen in: <file / command / message>.

## Most likely degradation
- Degradation: <failure mode>
- Prevention: <action>
```

Translate the headings into the reply language. If nothing is unfinished, write "None" under that heading rather than dropping it.
