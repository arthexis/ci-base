#!/usr/bin/env python3
"""Generate a standalone Python repository from ci-base's vendored templates."""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def initialize(target: Path, name: str, *, ansible: bool) -> None:
    if not NAME.fullmatch(name):
        raise ValueError("project name must be lowercase kebab-case")
    if target.exists() and any(target.iterdir()):
        raise ValueError("target directory must be empty")
    target.mkdir(parents=True, exist_ok=True)
    package = name.replace("-", "_")
    (target / "src" / package).mkdir(parents=True)
    (target / "src" / package / "__init__.py").write_text('__version__ = "0.1.0"\n')
    (target / "tests").mkdir()
    (target / "tests" / "test_smoke.py").write_text(
        f"from {package} import __version__\n\ndef test_version():\n    assert __version__\n"
    )
    (target / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools>=68"]\nbuild-backend = "setuptools.build_meta"\n\n'
        f'[project]\nname = "{name}"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n\n'
        '[tool.setuptools.packages.find]\nwhere = ["src"]\n\n'
        '[tool.ruff]\nline-length = 100\n'
    )
    (target / "README.md").write_text(
        f"# {name}\n\nGenerated from ci-base. Customize the application and CI commands.\n"
    )
    (target / ".gitignore").write_text(".venv/\n__pycache__/\n.pytest_cache/\n*.egg-info/\ndist/\nbuild/\n")
    workflows = target / ".github" / "workflows"
    workflows.mkdir(parents=True)
    for workflow in sorted((ROOT / "templates" / "workflows").glob("*.yml")):
        if workflow.name == "ansible.yml" and not ansible:
            continue
        shutil.copy2(workflow, workflows / workflow.name)
    if ansible:
        source = ROOT / "templates" / "deployment"
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("README.md", ".gitignore"))
        defaults = target / "ansible" / "roles" / "app" / "defaults" / "main.yml"
        defaults.write_text(defaults.read_text().replace("example-app", name))
        deploy = target / "deploy.sh"
        deploy.chmod(deploy.stat().st_mode | 0o111)
        (target / "README.md").write_text(
            (target / "README.md").read_text()
            + "\nDeployment scaffold is included but must be adapted before production use.\n"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="lowercase kebab-case project name")
    parser.add_argument("--output", type=Path, help="output directory (default: ./<name>)")
    parser.add_argument("--ansible", action="store_true", help="include deployment scaffold")
    args = parser.parse_args(argv)
    try:
        initialize((args.output or Path(args.name)).resolve(), args.name, ansible=args.ansible)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Created {args.name} in {(args.output or Path(args.name)).resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
