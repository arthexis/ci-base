from pathlib import Path

import audit


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_workflow_audit_accepts_canonical_contract(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    _write(
        workflows / "quality.yml",
        """name: python / Quality\n\njobs:\n  quality:\n    name: python / Quality\n    steps:\n      - run: python -m ruff check --config pyproject.toml .\n      - run: python -m ruff format --check --config pyproject.toml .\n""",
    )
    for filename, check_name in (
        ("package.yml", "python / Package"),
        ("python-compatibility.yml", "python / Python compatibility"),
        ("clean-install.yml", "Clean Install"),
    ):
        _write(
            workflows / filename,
            f"""name: {check_name}\n\njobs:\n  quality:\n    name: Quality gate\n    steps:\n      - run: python -m ruff check --config pyproject.toml .\n      - run: python -m ruff format --check --config pyproject.toml .\n  main:\n    name: {check_name}\n    needs: quality\n""",
        )

    findings = audit.audit_workflows(tmp_path)

    assert findings == []


def test_ruleset_audit_detects_legacy_ci_base_contexts() -> None:
    ruleset = {
        "rules": [
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [
                        {"context": "ci-base baseline / python / Quality"},
                        {"context": "ci-base baseline / python / Package"},
                    ]
                },
            }
        ]
    }

    findings = audit.audit_ruleset(ruleset)

    assert any("legacy ci-base context" in finding for finding in findings)
    assert any("missing required context: Clean Install" in finding for finding in findings)
