---
name: check-stage-ready
description: Use when about to submit a stage branch for mentor review, or when wanting to verify all stage requirements are implemented and tests pass.
context: fork
argument-hint: "[stage-number]"
allowed-tools: Read, Glob, Bash
---

# Check Stage Ready

Verify a stage implementation is complete before submitting to the mentor.

## What to do

You receive a stage number as `$ARGUMENTS` (e.g., `1`).

**Step 1 — Read the spec**

Read `Documents/stage$ARGUMENTS.md` to get the list of features/requirements for this stage.

**Step 2 — Read the plan**

Read `docs/stage$ARGUMENTS-plan.md` to get the task checklist.

**Step 3 — Check required files exist and are non-empty**

Glob for all Python files referenced in the plan (app/, config.py, main.py, tests/). For each:
- Check it exists
- Check it has content (not just a placeholder/empty file)

**Step 4 — Run the test suite**

Run: `uv run pytest --tb=short -q`

Capture the output.

**Step 5 — Output a readiness report**

Print a markdown checklist in this format:

```
## Stage N Readiness Report

### Spec requirements
- [x] requirement from spec that is implemented
- [ ] requirement that appears missing

### Files
- [x] app/db/models.py — has content
- [ ] app/agent/nodes.py — empty

### Tests
- [x] X passed, Y failed
- [ ] failing: test_name — short reason

### Verdict
READY / NOT READY — [one sentence summary]
```

Be honest. If a file exists but only contains a comment or `pass`, mark it as not implemented.
