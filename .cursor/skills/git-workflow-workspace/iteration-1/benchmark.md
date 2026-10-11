# git-workflow eval, iteration 1

Each test ran once with the skill and once without it, in a throwaway copy of a small project. Code checks read the git history. Two checks needed a judge because they depend on the wording of the reply.

| Test | With the skill | Without the skill |
| --- | --- | --- |
| README offline note | 5 of 6 | 5 of 6 |
| Timeout in .env | 4 of 4 | 3 of 4 |
| Asked to merge | 3 of 3 | 0 of 3 |
| **All checks** | **12 of 13** | **8 of 13** |

The skill passed 4 more checks. The difference is the timeout branch name and the refusal to merge.

Token counts and per-run times were not reported. The six runs started together at 14:44 and had finished before grading at 14:48.
