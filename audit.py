#!/usr/bin/env python3
"""Audit local CI workflow contracts and GitHub required status checks."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

WORKFLOW_DIR = Path(".github/workflows")
REQUIRED_CONTEXTS = (
    "python / Quality",
    "python / Package",
    "python / Python compatibility",
    "Clean Install",
)
DOWNSTREAM_CONTEXTS = REQUIRED_CONTEXTS[1:]
RUFF_CHECK = "python -m ruff check --config pyproject.toml"
RUFF_FORMAT = "python -m ruff format --check --config pyproject.toml"


def _workflow_files(target: Path) -> list[Path]:
    root = target / WORKFLOW_DIR
    return sorted([*root.glob("*.yml"), *root.glob("*.yaml")]) if root.exists() else []


def _jobs(text: str) -> dict[str, dict[str, Any]]:
    """Extract the small YAML subset needed for workflow job auditing."""
    lines = text.splitlines()
    jobs: dict[str, dict[str, Any]] = {}
    in_jobs = False
    current: str | None = None

    for line in lines:
        if line == "jobs:":
            in_jobs = True
            current = None
            continue
        if not in_jobs:
            continue
        if line and not line.startswith(" "):
            break

        job_match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if job_match:
            current = job_match.group(1)
            jobs[current] = {"name": None, "needs": [], "lines": []}
            continue
        if current is None:
            continue

        jobs[current]["lines"].append(line)
        name_match = re.match(r"^    name:\s*['\"]?(.+?)['\"]?\s*$", line)
        if name_match:
            jobs[current]["name"] = name_match.group(1)
            continue
        needs_match = re.match(r"^    needs:\s*(.+?)\s*$", line)
        if needs_match:
            value = needs_match.group(1).strip()
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]
            jobs[current]["needs"] = [
                item.strip().strip("'\"") for item in value.split(",") if item.strip()
            ]

    return jobs


def _job_index(target: Path) -> dict[str, tuple[Path, str, dict[str, Any]]]:
    index: dict[str, tuple[Path, str, dict[str, Any]]] = {}
    for path in _workflow_files(target):
        text = path.read_text(encoding="utf-8")
        for job_id, job in _jobs(text).items():
            name = job.get("name")
            if name in REQUIRED_CONTEXTS:
                index[name] = (path, job_id, job)
    return index


def _has_quality_commands(text: str) -> bool:
    return RUFF_CHECK in text and RUFF_FORMAT in text


def _depends_on_quality(
    jobs: dict[str, dict[str, Any]], job_id: str, seen: set[str] | None = None
) -> bool:
    if job_id == "quality":
        return True
    if seen is None:
        seen = set()
    if job_id in seen:
        return False
    seen.add(job_id)

    job = jobs.get(job_id)
    if job is None:
        return False
    return any(_depends_on_quality(jobs, dependency, seen) for dependency in job.get("needs", []))


def audit_workflows(target: Path) -> list[str]:
    findings: list[str] = []
    index = _job_index(target)

    for context in REQUIRED_CONTEXTS:
        if context not in index:
            findings.append(f"missing workflow check: {context}")

    quality = index.get("python / Quality")
    if quality is not None:
        path, _, _ = quality
        if not _has_quality_commands(path.read_text(encoding="utf-8")):
            findings.append(
                f"{path}: Quality must run Ruff check and format with --config pyproject.toml"
            )

    for context in DOWNSTREAM_CONTEXTS:
        entry = index.get(context)
        if entry is None:
            continue
        path, job_id, _ = entry
        text = path.read_text(encoding="utf-8")
        jobs = _jobs(text)
        if not _depends_on_quality(jobs, job_id):
            findings.append(f"{path}: {context} must depend on quality before running")
        quality_job = jobs.get("quality")
        if quality_job is None:
            findings.append(f"{path}: missing leading quality job")
        elif not _has_quality_commands("\n".join(quality_job.get("lines", []))):
            findings.append(
                f"{path}: quality gate must use Ruff with --config pyproject.toml"
            )

    return findings


def _required_contexts_from_ruleset(ruleset: dict[str, Any]) -> set[str]:
    contexts: set[str] = set()
    for rule in ruleset.get("rules", []):
        if rule.get("type") != "required_status_checks":
            continue
        checks = rule.get("parameters", {}).get("required_status_checks", [])
        contexts.update(
            check.get("context") for check in checks if isinstance(check.get("context"), str)
        )
    return contexts


def audit_ruleset(ruleset: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    contexts = _required_contexts_from_ruleset(ruleset)

    for context in sorted(contexts):
        if context.startswith("ci-base baseline /"):
            findings.append(f"legacy ci-base context: {context}")

    expected = set(REQUIRED_CONTEXTS)
    for context in REQUIRED_CONTEXTS:
        if context not in contexts:
            findings.append(f"missing required context: {context}")
    for context in sorted(contexts - expected):
        findings.append(f"unexpected required context: {context}")

    required_rule = next(
        (rule for rule in ruleset.get("rules", []) if rule.get("type") == "required_status_checks"),
        None,
    )
    if required_rule is None:
        findings.append("missing required_status_checks rule")
    elif not required_rule.get("parameters", {}).get("strict_required_status_checks_policy", False):
        findings.append("required status checks should require the branch to be up to date")

    return findings


def _infer_repo(target: Path) -> str | None:
    try:
        url = subprocess.check_output(
            ["git", "-C", str(target), "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None

    match = re.search(r"github\.com[/:]([^/]+/[^/.]+)(?:\.git)?$", url)
    return match.group(1) if match else None


def _github_json(url: str) -> Any:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ci-base-audit"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def fetch_default_branch_ruleset(repo: str) -> dict[str, Any]:
    base = f"https://api.github.com/repos/{repo}"
    rulesets = _github_json(f"{base}/rulesets")
    candidates = [item for item in rulesets if item.get("target") == "branch"]
    if not candidates:
        raise RuntimeError(f"{repo}: no branch ruleset found")

    detailed = [_github_json(f"{base}/rulesets/{item['id']}") for item in candidates]
    for ruleset in detailed:
        include = ruleset.get("conditions", {}).get("ref_name", {}).get("include", [])
        if "~DEFAULT_BRANCH" in include:
            return ruleset
    if len(detailed) == 1:
        return detailed[0]
    raise RuntimeError(f"{repo}: no default-branch ruleset found")


def audit(target: Path, repo: str | None = None, check_ruleset: bool = True) -> int:
    findings = audit_workflows(target)

    if check_ruleset:
        resolved_repo = repo or _infer_repo(target)
        if not resolved_repo:
            findings.append("ruleset not checked: pass --repo owner/name or configure origin")
        else:
            try:
                findings.extend(audit_ruleset(fetch_default_branch_ruleset(resolved_repo)))
            except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError) as exc:
                findings.append(f"ruleset check failed: {exc}")

    if findings:
        for finding in findings:
            print(f"FAIL  {finding}")
        return 1

    print("PASS  workflow contract")
    if check_ruleset:
        print("PASS  ruleset contract")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit local CI workflow and required-status-check contracts."
    )
    parser.add_argument("target", nargs="?", default=".", type=Path)
    parser.add_argument("--repo", help="GitHub repository as owner/name; inferred from origin by default")
    parser.add_argument(
        "--no-ruleset",
        action="store_true",
        help="skip the GitHub ruleset check",
    )
    args = parser.parse_args()
    return audit(
        args.target.resolve(),
        repo=args.repo,
        check_ruleset=not args.no_ruleset,
    )


if __name__ == "__main__":
    raise SystemExit(main())
