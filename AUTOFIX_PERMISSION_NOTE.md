# Ruff autofix permission boundary

Reusable workflows cannot elevate `GITHUB_TOKEN` permissions above those granted by the caller. A shared CI workflow that requests `contents: write` or `actions: write` therefore causes startup failures for consumers whose workflow grants only read access.

The shared CI baseline must remain read-only. Any future branch-mutating autofix workflow should be exposed as a separate opt-in workflow that consumers call explicitly with the required write permissions.
