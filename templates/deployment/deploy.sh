#!/usr/bin/env bash
set -euo pipefail
if [[ "${EUID}" -eq 0 ]]; then echo "Run as a non-root operator" >&2; exit 1; fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
if [[ "${1:-}" == "--check" ]]; then
  shift
  exec ansible-playbook -i ansible/inventory/localhost.yml ansible/playbooks/install.yml --check --diff "$@"
fi
exec ansible-playbook -i ansible/inventory/localhost.yml ansible/playbooks/install.yml "$@"
