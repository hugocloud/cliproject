---
name: pr-review
description: Reviews pull requests for code quality. Use when reviewing PRs or checking code changes, or when the user runs /pr-review.
---

## Resolving the target

The skill may be invoked with an optional argument identifying what to review:
- No argument: review the current uncommitted/staged diff (`git diff` / `git diff --staged`) plus any commits ahead of the default branch on the current branch.
- A number (e.g. `4`): treat as a PR number and fetch the diff with `gh pr diff <number>`.
- A URL containing `/pull/`: treat as a PR URL and fetch the diff with `gh pr diff <url>`.
- Anything else (e.g. `feat/TCK-0001/Request-loan`): treat as a branch name and diff it against the default branch: `git diff origin/master...<branch>` (or `master...<branch>` if there's no remote tracking branch).

Once the diff is resolved, review it against the checklist below.

## Code Quality

1. **Readability and clear naming** - Variables, functions and classes should have descriptive names.
