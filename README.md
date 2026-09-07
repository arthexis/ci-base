# ci-base

Generic CI foundation and GitHub repository template for Arthexis Python projects.

The goal is to provide a small, reusable baseline for linting, formatting, tests, package builds, clean-install smoke checks, and repository-health validation while leaving project-specific integration checks in each consuming repository.

## Baseline

Generated repositories get a default `CI` workflow that runs on pull requests and pushes to `main`. It calls the centrally maintained `arthexis/ci-base/.github/workflows/consumer-ci.yml@v1` workflow with these defaults:

- Python 3.13
- `ruff check .`
- `ruff format --check .`
- `pytest`
- wheel and sdist build via `python -m build`
- clean wheel installation followed by `pip check`
- read-only GitHub token permissions

The `v1` branch is the compatibility line for non-breaking CI improvements. Breaking policy changes should use a future major line such as `v2` so consuming repositories can opt in deliberately.

The reusable workflow accepts inputs for the Python version, install command, test command, lint paths, package build, and clean-install check.

## Repository validator

The template includes a small standard-library-only validator:

```console
python .ci/check_repo.py
```

For a generated Python repository it checks that the repository has:

- a README
- `.github/workflows/ci.yml`
- a valid `pyproject.toml` with `[project]` name and version
- a `tests/` directory containing at least one `test_*.py` module

`ci-base` validates its own template-level structure with:

```console
python .ci/check_repo.py --template
```

The validator intentionally has no third-party dependencies, so it can run before project dependencies are installed and can later grow into the common repository-health entry point.

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

For simple changes, edit `.github/workflows/ci.yml` and pass inputs to the central workflow, for example:

```yaml
jobs:
  python:
    uses: arthexis/ci-base/.github/workflows/consumer-ci.yml@v1
    with:
      python-version: "3.12"
      install-command: python -m pip install -e ".[test]"
      test-command: python -m pytest tests
```

The template intentionally keeps project metadata and dependencies local to each repository rather than trying to share a universal `pyproject.toml`.
