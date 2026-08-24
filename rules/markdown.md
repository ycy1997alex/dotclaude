---
name: markdown
description: Formatting conventions for markdown source — line wrapping and blank-line separation.
paths:
  - "**/*.md"
---

# Markdown formatting

These rules govern the *source* file, not the rendered output. They exist because markdown is read by both renderers and models, and the two disagree about what a single newline means.

## No hard wrapping

Write each paragraph, list item, or table row as one physical line, however long. Do not fold prose to a fixed column width.

A single newline inside a paragraph is a soft break in CommonMark but a literal `<br>` under GitHub-flavored markdown and several editor previews. Wrapped source therefore renders with breaks in the middle of sentences, at whatever column the wrap happened to fall on. Long lines cost nothing — every editor soft-wraps for display.

The exception is fenced code blocks, where line breaks are content and must be preserved exactly as written.

## Blank line before and after block elements

Separate every block from its neighbours with one blank line: paragraphs, headings, lists, tables, code fences, and block quotes.

A list that touches the paragraph below it gets parsed as a continuation of the final list item, so the paragraph silently becomes part of the bullet. The same applies to a heading pressed against the text above it. One blank line removes the ambiguity for every parser.

Use exactly one blank line — consecutive blank lines carry no meaning and only add noise to diffs.

## Verification

After editing a markdown file, check that no paragraph is split across physical lines and that every heading, list, and fence is bounded by blank lines. Both are visible in the raw source; no renderer is needed.
