# ci-base

Canonical CI templates and audit tooling for Arthexis Python repositories.

`ci-base` is a **reference/template repository**, not a runtime workflow service. Consumer repositories should copy the workflow templates they need into their own `.github/workflows/` directory and then own those files locally. They should not call workflows from `arthexis/ci-base` with `uses:`.

This keeps CI execution, permissions, tokens, failures, and repository-specific customizations local to each project while preserving a common baseline that can be reviewed when useful.

## Workflow templates

The canonical workflow templates live in `templates/workflows/`:

- `quality.yml` — Ruff lint and format checks
- `python-compatibility.yml` — test matrix and compatibility aggregate
- `package.yml` — build distributions and verify wheel installation
- `clean-install.yml` — independent clean-install smoke check

Copy them into a consumer repository rather than referencing this repository at runtime. Projects are expected to customize commands, supported Python versions, extras, services, and smoke checks as needed.

The templates intentionally favor independent workflows so required GitHub status checks remain explicit and repository-local.

## Optional divergence audit

`audit.py` compares the canonical templates with a repository's local workflows:

```console
python audit.py ../some-repository
python audit.py ../some-repository --diff
```

It reports each canonical workflow as `MATCH`, `MISSING`, or `DIVERGED`. With `--diff`, divergent files include a unified diff.

A divergent workflow is not inherently wrong: projects may need local differences. The audit exists to make those differences visible for review. It is **not** part of the required CI baseline and does not update or modify consumer repositories.

## Local quality helper

`.ci/quality.sh` remains available as a lightweight reference for local Ruff checks:

```console
bash .ci/quality.sh --fix src tests
bash .ci/quality.sh --check src tests
```

Consumers may copy or adapt it if useful.

## Repository validator

The standard-library-only validator remains available:

```console
python .ci/check_repo.py
```

For a generated Python repository it checks basic repository structure such as the README, workflow presence, `pyproject.toml`, and tests. `ci-base` can validate its template-level structure with:

```console
python .ci/check_repo.py --template
```

## Design rule

`ci-base` defines a recommended starting point, not centrally enforced behavior. Changes here do not automatically alter existing repositories. Adoption of template updates should happen deliberately, normally through a PR in the consumer repository after reviewing any divergence reported by `audit.py`.

## Optional self-contained Ansible starter

A copyable starter lives in [templates/deployment](templates/deployment/README.md).
It provides a local `deploy.sh`, a local inventory, an Ansible role, optional
systemd unit, immutable release directory convention, verification playbook,
and minimal contract tests. Copy its **contents** into the consumer repository
and adapt the placeholder application installation before any production deploy.

Copy `templates/workflows/ansible.yml` to the consumer's
`.github/workflows/ansible.yml` to validate Ansible locally. This workflow
never invokes ci-base or a remote server. The default inventory targets
localhost only. Deployment to real hosts is explicitly configured by each
consumer; no secrets or hostnames are shipped.

The Ansible starter is **optional** for libraries and non-deployable projects.
It is not an operational deployment of an application out of the box.

### GitHub template repository

After this PR passes checks and is merged, enable **Settings → General →
Template repository**. GitHub will let you generate a new repository with
a snapshot of the files; future template changes do not propagate
automatically. Copying the CI/Ansible templates into a new repository is a
deliberate initialization step, not a runtime dependency.
