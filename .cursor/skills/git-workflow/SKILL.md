---
name: git-workflow
description: >-
  Follows the project git workflow whenever code is changed: branch off main,
  keep secrets out of commits, push the branch, and open a pull request for a
  person to merge. Use when editing files, committing, pushing, opening a pull
  request, or any time repository files are modified.
---

Never work on main. Before changing code, pull main and create a branch: feat/... for features, fix/... for bugs, docs/... for docs.
Never commit .env or other secrets.
When the work is done, push the branch and open a PR to main, with a short description: what changed, why, and how it was tested.
Never merge the PR. A person merges, after review and green CI.
