from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class DeploymentContract(unittest.TestCase):
    def test_local_inventory(self):
        inventory = (ROOT / "ansible/inventory/localhost.yml").read_text()
        self.assertIn("ansible_connection: local", inventory)

    def test_release_is_versioned(self):
        tasks = (ROOT / "ansible/roles/app/tasks/main.yml").read_text()
        self.assertIn("releases/{{ app_release_id }}", tasks)
        self.assertIn('state: link', tasks)

    def test_no_cross_repo_workflow(self):
        # This starter has no reusable workflow dependency.
        self.assertNotIn("uses: arthexis/", (ROOT / "README.md").read_text())
