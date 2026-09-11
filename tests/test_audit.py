from pathlib import Path

import audit


def test_templates_pass_workflow_audit(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    template_dir = Path(__file__).resolve().parents[1] / "templates" / "workflows"

    for template in template_dir.glob("*.yml"):
        (workflows / template.name).write_text(template.read_text(encoding="utf-8"), encoding="utf-8")

    assert audit.audit_workflows(tmp_path) == []


def test_canonical_ruleset_passes() -> None:
    ruleset = {
        "rules": [
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [
                        {"context": context} for context in audit.REQUIRED_CONTEXTS
                    ],
                },
            }
        ]
    }

    assert audit.audit_ruleset(ruleset) == []


def test_ruleset_audit_detects_legacy_ci_base_contexts() -> None:
    ruleset = {
        "rules": [
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [
                        {"context": "ci-base baseline / python / Quality"},
                        {"context": "ci-base baseline / python / Package"},
                        {"context": "ci-base baseline / python / Python compatibility"},
                        {"context": "ci-base baseline / Branch current"},
                    ],
                },
            }
        ]
    }

    findings = audit.audit_ruleset(ruleset)

    assert any("legacy ci-base context" in finding for finding in findings)
    assert any("missing required context: Clean Install" in finding for finding in findings)
    assert any("unexpected required context: ci-base baseline / Branch current" in finding for finding in findings)
