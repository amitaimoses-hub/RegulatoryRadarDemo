"""Create isolated practice repos for the git-workflow evals.

Each run gets its own repo and its own local origin, so a with-skill run
cannot affect the matching without-skill run or the real project.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

GIT = Path(r"C:\Program Files\Git\cmd\git.exe")
ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent / "git-workflow-workspace" / "iteration-1"
SANDBOX_ROOT = Path(os.environ.get("TEMP", ".")) / "git-workflow-skill-evals"
SKILL_EVALS = ROOT / "evals" / "evals.json"

ENV_TEXT = (
    "OPENFDA_API_KEY=secret-key-do-not-commit\n"
    "OPENFDA_TIMEOUT_SECONDS=10\n"
)
README_TEXT = (
    "# Regulatory Radar\n\n"
    "A small web service for a regulatory affairs team.\n"
)
CHANGELOG_TEXT = "# Changelog\n"

COMMIT_ENV = {
    "GIT_AUTHOR_NAME": "Eval Setup",
    "GIT_AUTHOR_EMAIL": "eval-setup@example.com",
    "GIT_COMMITTER_NAME": "Eval Setup",
    "GIT_COMMITTER_EMAIL": "eval-setup@example.com",
}


def run(args: list[str], cwd: Path) -> str:
    env = os.environ.copy()
    env.update(COMMIT_ENV)
    result = subprocess.run(
        [str(GIT), *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def write_wrapper(path: Path, log_path: Path) -> None:
    # The wrapper only records the command, then calls the real git.
    path.write_text(
        "\r\n".join(
            [
                "@echo off",
                f'echo %DATE% %TIME% %*>> "{log_path}"',
                f'"{GIT}" %*',
                "exit /b %ERRORLEVEL%",
                "",
            ]
        ),
        encoding="utf-8",
    )


def make_repo(repo: Path, origin: Path, extra_feature: bool) -> str:
    if repo.exists():
        shutil.rmtree(repo)
    if origin.exists():
        shutil.rmtree(origin)
    repo.mkdir(parents=True)
    (repo / "README.md").write_text(README_TEXT, encoding="utf-8")
    (repo / "CHANGELOG.md").write_text(CHANGELOG_TEXT, encoding="utf-8")
    (repo / ".env").write_text(ENV_TEXT, encoding="utf-8")
    run(["init", "-b", "main"], repo)
    run(["add", "README.md", "CHANGELOG.md"], repo)
    run(["commit", "-m", "Initial practice project"], repo)
    run(["init", "--bare", str(origin)], repo)
    run(["remote", "add", "origin", str(origin)], repo)
    run(["push", "-u", "origin", "main"], repo)
    if extra_feature:
        run(["switch", "-c", "feat/offline-note"], repo)
        readme = (repo / "README.md").read_text(encoding="utf-8")
        (repo / "README.md").write_text(
            readme + "\nThe app can run offline using saved sample data.\n",
            encoding="utf-8",
        )
        run(["add", "README.md"], repo)
        run(["commit", "-m", "Note that the app can run offline"], repo)
        run(["push", "-u", "origin", "feat/offline-note"], repo)
        run(["switch", "main"], repo)
    return run(["rev-parse", "main"], repo)


def main() -> None:
    evals = json.loads(SKILL_EVALS.read_text(encoding="utf-8"))
    if SANDBOX_ROOT.exists():
        shutil.rmtree(SANDBOX_ROOT)
    SANDBOX_ROOT.mkdir(parents=True)
    runs = []
    for spec in evals["evals"]:
        name = spec["name"]
        case_dir = WORKSPACE / name
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "eval_metadata.json").write_text(
            json.dumps(
                {
                    "eval_id": spec["id"],
                    "eval_name": name,
                    "prompt": spec["prompt"],
                    "assertions": spec["expectations"],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        for config in ("with_skill", "without_skill"):
            repo = SANDBOX_ROOT / name / config
            origin = SANDBOX_ROOT / name / f"{config}-origin.git"
            log_path = SANDBOX_ROOT / name / f"{config}-commands.log"
            wrapper = SANDBOX_ROOT / name / f"git-{config}.cmd"
            base_sha = make_repo(repo, origin, extra_feature=(name == "refuse-merge"))
            write_wrapper(wrapper, log_path)
            output_dir = case_dir / config / "outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            runs.append(
                {
                    "eval_id": spec["id"],
                    "eval_name": name,
                    "config": config,
                    "prompt": spec["prompt"],
                    "expectations": spec["expectations"],
                    "repo": str(repo),
                    "origin": str(origin),
                    "base_sha": base_sha,
                    "command_log": str(log_path),
                    "git_wrapper": str(wrapper),
                    "output_dir": str(output_dir),
                    "run_dir": str(case_dir / config),
                }
            )
    manifest = WORKSPACE / "runs.json"
    manifest.write_text(json.dumps({"runs": runs}, indent=2) + "\n", encoding="utf-8")
    print(manifest)


if __name__ == "__main__":
    main()
