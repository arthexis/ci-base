#!/usr/bin/env python3
"""Compare a repository's local CI workflows with the ci-base templates."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "workflows"


def audit(target: Path, show_diff: bool = False) -> int:
    workflow_dir = target / ".github" / "workflows"
    templates = sorted(TEMPLATE_DIR.glob("*.yml"))
    divergent = False

    for template in templates:
        local = workflow_dir / template.name
        if not local.exists():
            print(f"MISSING   {local}")
            divergent = True
            continue

        expected = template.read_text(encoding="utf-8").splitlines(keepends=True)
        actual = local.read_text(encoding="utf-8").splitlines(keepends=True)
        if expected == actual:
            print(f"MATCH     {local}")
            continue

        print(f"DIVERGED  {local}")
        divergent = True
        if show_diff:
            print(
                "".join(
                    difflib.unified_diff(
                        expected,
                        actual,
                        fromfile=f"template/{template.name}",
                        tofile=str(local),
                    )
                ),
                end="",
            )

    return 1 if divergent else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report whether local workflows diverge from ci-base templates."
    )
    parser.add_argument("target", nargs="?", default=".", type=Path)
    parser.add_argument("--diff", action="store_true", help="show unified diffs")
    args = parser.parse_args()
    return audit(args.target.resolve(), show_diff=args.diff)


if __name__ == "__main__":
    raise SystemExit(main())
