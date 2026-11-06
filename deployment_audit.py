#!/usr/bin/env python3
"""Read-only audit of a repository's standalone deployment contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CHECKS = {
    "deploy-wrapper": "deploy.sh",
    "ansible-install": "ansible/playbooks/install.yml",
    "ansible-verify": "ansible/playbooks/verify.yml",
    "ansible-role": "ansible/roles/app/tasks/main.yml",
    "ansible-ci": ".github/workflows/ansible.yml",
}


def audit(root: Path) -> dict[str, object]:
    checks = {key: (root / path).is_file() for key, path in CHECKS.items()}
    warnings = []
    workflows = root / ".github" / "workflows"
    for file in sorted(workflows.glob("*.yml")) if workflows.exists() else []:
        content = file.read_text(encoding="utf-8")
        if "arthexis/ci-base/.github/workflows/" in content:
            warnings.append(f"{file.name}: cross-repository workflow dependency")
    return {"checks": checks, "missing": [k for k, ok in checks.items() if not ok], "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(args.repository)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, ok in result["checks"].items():
            print(f"{'PASS' if ok else 'MISSING'} {key}")
        for warning in result["warnings"]:
            print(f"WARNING {warning}")
        if result["missing"]:
            print("Recommendation: adopt the standalone Ansible starter, then customize deployment.")
    return int(bool(result["missing"] or result["warnings"]))


if __name__ == "__main__":
    raise SystemExit(main())
