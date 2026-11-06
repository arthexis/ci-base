# Self-contained Ansible deployment starter

Copy the contents of this directory to the new repository root. Copy
`../workflows/ansible.yml` into `.github/workflows/ansible.yml`.
The existing CI workflow templates are copied separately.

## Adapt before deploying

1. Replace `example-app` in `ansible/roles/app/defaults/main.yml`.
2. Replace the marker-only task with installation of the real application artifact.
3. Set `app_release_id` to an immutable commit SHA (or artifact digest) in production.
4. Enable the systemd unit only when a real service command is configured.
5. Configure a target inventory and credentials outside source control.
6. Validate `ansible-playbook --syntax-check` and run twice on a disposable Linux host;
   the second run should report zero changes.

`./deploy.sh` deploys locally. `./deploy.sh --check` runs check mode.
The default localhost inventory is deliberately safe: CI must not access production.
Run `ansible-playbook -i <inventory> ansible/playbooks/install.yml` for remote targets.

The included release marker and service are scaffolding, **not** a working application.
The release directory is versioned; the `current` symlink selects the active version.
Do not mutate a published release in production. Keep persistent data outside releases.

No workflows call ci-base or other repositories at runtime.
