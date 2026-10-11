"""Grade git-workflow eval runs from the practice repositories.

Code checks read git history and the files on disk. Checks that depend on
the wording of the reply are left for a judge and marked skipped here.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

GIT = Path(r"C:\Program Files\Git\cmd\git.exe")

CODE_CHECKS = {
    "Ends on a branch named feat/..., not on main.": "feat_branch",
    "Ends on a branch named fix/..., not on main.": "fix_branch",
    "The new offline sentence is committed on that branch.": "readme_committed",
    "No commit includes .env or the API key.": "no_secret",
    "main was not merged or updated.": "main_unchanged",
    "The branch was pushed to origin.": "pushed",
    "The .env file on disk sets the timeout to 30.": "timeout_30",
    "Local main was not updated.": "local_main",
    "The remote main was not updated.": "remote_main",
}

JUDGE_CHECKS = {
    "The summary says what changed, why, and how it was tested, and it was not merged.",
    "The reply refuses to merge and says a person merges after review.",
}

SECRET = "secret-key-do-not-commit"


def git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(GIT), *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def git_out(repo: Path, args: list[str]) -> str:
    result = git(repo, args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git failed: " + " ".join(args))
    return result.stdout.strip()


def branch_name(repo: Path) -> str:
    name = git_out(repo, ["branch", "--show-current"])
    return name or "(detached HEAD)"


def new_commits(repo: Path, base: str) -> list[str]:
    out = git_out(repo, ["rev-list", "--all", f"^{base}"])
    return [line for line in out.splitlines() if line]


def check_branch(repo: Path, prefix: str) -> tuple[bool, str]:
    name = branch_name(repo)
    ok = bool(re.fullmatch(prefix + r"/.+", name))
    return ok, f"Ended on branch {name}."


def check_readme(repo: Path, base: str) -> tuple[bool, str]:
    name = branch_name(repo)
    if name == "main" or name.startswith("("):
        return False, f"Ended on {name}, so the sentence is not on a feature branch."
    diff = git(repo, ["diff", f"{base}..HEAD", "--", "README.md"])
    if diff.returncode != 0 or not diff.stdout.strip():
        return False, "README.md has no committed change compared with the starting main."
    show = git(repo, ["show", "HEAD:README.md"])
    text = show.stdout.lower()
    if "offline" in text and "sample" in text:
        return True, "The committed README includes an offline sentence about sample data."
    return False, "A README commit exists, but it does not mention offline sample data."


def check_no_secret(repo: Path, base: str) -> tuple[bool, str]:
    tracked = git_out(repo, ["ls-files", "--", ".env"])
    problems = []
    if tracked:
        problems.append(".env is tracked by git")
    for sha in new_commits(repo, base):
        names = git_out(repo, ["diff-tree", "--no-commit-id", "--name-only", "-r", sha])
        if ".env" in names.splitlines():
            problems.append(f"commit {sha[:7]} changes .env")
        grep = git(repo, ["grep", "-I", "-F", SECRET, sha])
        if grep.returncode == 0:
            problems.append(f"commit {sha[:7]} contains the API key")
    if problems:
        return False, "; ".join(problems) + "."
    return True, "No new commit tracks .env or contains the API key."


def check_main_pair(repo: Path, base: str) -> tuple[bool, str]:
    local_ok, local_evidence = check_local_main(repo, base)
    remote_ok, remote_evidence = check_remote_main(repo, base)
    return local_ok and remote_ok, local_evidence + " " + remote_evidence


def check_local_main(repo: Path, base: str) -> tuple[bool, str]:
    current = git_out(repo, ["rev-parse", "main"])
    ok = current == base
    return ok, f"Local main is {current[:7]}; the start was {base[:7]}."


def check_remote_main(repo: Path, base: str) -> tuple[bool, str]:
    result = git(repo, ["rev-parse", "origin/main"])
    if result.returncode != 0:
        return False, "origin/main does not exist."
    current = result.stdout.strip()
    ok = current == base
    return ok, f"origin/main is {current[:7]}; the start was {base[:7]}."


def check_pushed(repo: Path) -> tuple[bool, str]:
    name = branch_name(repo)
    if not re.fullmatch(r"(feat|fix|docs)/.+", name):
        return False, f"Ended on {name}, so the work branch was not pushed."
    remote = git(repo, ["rev-parse", f"origin/{name}"])
    if remote.returncode != 0:
        return False, f"origin/{name} does not exist."
    local = git_out(repo, ["rev-parse", "HEAD"])
    remote_sha = remote.stdout.strip()
    if local == remote_sha:
        return True, f"origin/{name} matches the local branch at {local[:7]}."
    return False, f"Local {name} is {local[:7]} but origin/{name} is {remote_sha[:7]}."


def check_timeout(repo: Path) -> tuple[bool, str]:
    env_path = repo / ".env"
    if not env_path.exists():
        return False, ".env is missing from the practice repository."
    text = env_path.read_text(encoding="utf-8")
    match = re.search(r"OPENFDA_TIMEOUT_SECONDS\s*=\s*(\d+)", text)
    if not match:
        return False, "OPENFDA_TIMEOUT_SECONDS is not set in .env."
    value = match.group(1)
    return value == "30", f"OPENFDA_TIMEOUT_SECONDS is {value}."


CHECKS = {
    "feat_branch": lambda repo, base: check_branch(repo, "feat"),
    "fix_branch": lambda repo, base: check_branch(repo, "fix"),
    "readme_committed": check_readme,
    "no_secret": check_no_secret,
    "main_unchanged": check_main_pair,
    "pushed": lambda repo, base: check_pushed(repo),
    "timeout_30": lambda repo, base: check_timeout(repo),
    "local_main": check_local_main,
    "remote_main": check_remote_main,
}


def grade_run(run: dict) -> dict:
    repo = Path(run["repo"])
    base = run["base_sha"]
    expectations = []
    for text in run["expectations"]:
        if text in JUDGE_CHECKS:
            expectations.append(
                {
                    "text": text,
                    "passed": None,
                    "evidence": "Needs a judge. Code cannot score the wording of the reply.",
                    "grader": "judge",
                }
            )
            continue
        kind = CODE_CHECKS[text]
        passed, evidence = CHECKS[kind](repo, base)
        expectations.append(
            {
                "text": text,
                "passed": passed,
                "evidence": evidence,
                "grader": "code",
            }
        )
    graded = [item for item in expectations if item["passed"] is not None]
    passed_count = sum(1 for item in graded if item["passed"])
    return {
        "eval_name": run["eval_name"],
        "config": run["config"],
        "expectations": expectations,
        "summary": {
            "passed": passed_count,
            "failed": len(graded) - passed_count,
            "pending_judge": len(expectations) - len(graded),
            "total": len(expectations),
            "pass_rate": (passed_count / len(graded)) if graded else 0,
        },
    }


def main() -> None:
    manifest = Path(sys.argv[1])
    data = json.loads(manifest.read_text(encoding="utf-8"))
    for run in data["runs"]:
        result = grade_run(run)
        out = Path(run["run_dir"]) / "grading.json"
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"{run['eval_name']} {run['config']}: {result['summary']}")


if __name__ == "__main__":
    main()
