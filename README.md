# ci-base

Generic CI foundation and GitHub repository template for Arthexis Python projects.

The goal is to provide a small, reusable baseline for linting, formatting, tests, package builds, and clean-install smoke checks while leaving project-specific integration checks in each consuming repository.

## Baseline

Generated repositories get a default `CI` workflow that runs on pull requests and pushes to `main`. It delegates to a reusable Python workflow with these defaults:

- Python 3.13
- `ruff check .`
- `ruff format --check .`
- `pytest`
- wheel and sdist build via `python -m build`
- clean wheel installation followed by `pip check`
- read-only GitHub token permissions

The reusable workflow accepts inputs for the Python version, install command, test command, lint paths, package build, and clean-install check.

## Expected project shape

The default workflow assumes the generated repository is an installable Python project. At minimum, provide a `pyproject.toml` that can be installed with:

```console
python -m pip install -e .
```

Tests should be runnable with:

```console
python -m pytest
```

Project-specific services, databases, hardware, Django setup, privileged networking, or integration tests belong in the consuming repository rather than in `ci-base`.

## Customizing a generated repository

For simple changes, edit `.github/workflows/ci.yml` and pass inputs to the reusable workflow, for example:

```yaml
jobs:
  python:
    uses: ./.github/workflows/python-ci.yml
    with:
      python-version: "3.12"
      install-command: python -m pip install -e ".[test]"
      test-command: python -m pytest tests
```

The template intentionally keeps project metadata and dependencies local to each repository rather than trying to share a universal `pyproject.toml`.
