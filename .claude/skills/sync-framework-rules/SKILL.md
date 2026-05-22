---
name: sync-framework-rules
description: Use when a user asks to check if Claude's knowledge of a framework or library is current, or to create/update project rules based on live documentation. Triggered by phrases like "check docs for X", "are you up to date on X", "create rules for X", or after choosing a tech stack.
context: fork
agent: general-purpose
argument-hint: "[framework]"
allowed-tools: WebSearch WebFetch Read Write Edit
---

# Sync Framework Rules

You are running in an isolated context. Your job: check current documentation for `$ARGUMENTS` and write or update `.claude/rules/$ARGUMENTS.md` in the project.

## Step 1 — Check existing rules

Read `.claude/rules/$ARGUMENTS.md` if it exists. Note what's already there so you only update what's changed.

## Step 2 — Fetch current docs

Run 2–3 targeted searches:
- `"$ARGUMENTS deprecated 2025 migration guide"`
- `"$ARGUMENTS changelog breaking changes 2025"`
- `site:<official-docs-domain> migration OR changelog OR "what's new"`

Fetch the official migration guide if one exists. Prefer official docs over blog posts.

## Step 3 — Extract the delta

Identify:
- Classes/functions marked deprecated and their replacements
- Import path changes
- Current recommended patterns that differ from what an AI trained before 2025 would write by default
- Any new required arguments or configuration

## Step 4 — Write or update `.claude/rules/$ARGUMENTS.md`

Use this format:

```markdown
# <Framework> Rules

Current API (<year>). Do not use deprecated patterns.

## Deprecated — never use
| Deprecated | Replacement |
|---|---|
| `old_api()` | `new_api()` |

## Current patterns

[key imports + minimal code examples]
```

If the file already exists, update it in place. Never create a duplicate.

## Step 5 — Ensure CLAUDE.md has the import

Check if `@.claude/rules/$ARGUMENTS.md` appears in CLAUDE.md under `## Framework Rules`. Add it if missing. No duplicates.
