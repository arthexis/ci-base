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

### Generate a clean standalone project

```sh
python bootstrap.py my-service --ansible
# or omit --ansible for a Python-only library
```

This creates `my-service/` with only the selected project files: Python package,
local workflows, tests and optional Ansible. It does **not** copy audit tooling,
template catalog files or cross-repository workflow calls.

If using GitHub's **Use this template**, the initial repository contains the
ci-base catalog. Run `python bootstrap.py my-service --ansible`, then move
the generated project files to the repository root and remove the catalog
files before first use. For the cleanest result, generate locally and push
the generated directory to a new empty GitHub repository instead.

### Project profiles and deployment audit

```sh
python bootstrap.py sample-lib --profile python-library
python bootstrap.py sample-service --profile python-service
python bootstrap.py sample-appliance --profile ansible-service
python deployment_audit.py ../existing-repository --json
```

The generated Ansible role can install a prebuilt wheel with
`app_wheel_path` and run `app_healthcheck_command`. Use a unique
`APP_RELEASE_ID` per immutable artifact. Real applications must configure
their executable, service settings and health check; no production deployment
is performed by CI. The bootstrap validation workflow installs the starter
on its disposable Ubuntu runner twice and asserts the second run has zero
changes. This is a scaffold-level idempotence test, not a guarantee for a
consumer's customized playbooks.

`deployment_audit.py` reports missing deployment files and forbidden
cross-repository CI calls without modifying the target.

### ci-base's own CI

CI runs on pull requests, with standalone quality, wheel-build and Python
compatibility gates. The workflow retains the existing GitHub ruleset check
names (`exercise-reusable-ci / python / Quality`,
`exercise-reusable-ci / python / Package`, and
`exercise-reusable-ci / python / Python compatibility`) while no longer
calling another repository's workflows. The separate bootstrap validation
job exercises the generated Ansible starter. This mirrors the local validation
pattern used by CSMS and GWay Remote, rather than relying on reusable CI.
