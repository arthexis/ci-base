from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import initialize
from deployment_audit import audit


def test_audit_generated_ansible_project():
    with TemporaryDirectory() as directory:
        root = Path(directory) / "service"
        initialize(root, "service", profile="ansible-service")
        result = audit(root)
        assert not result["missing"]
        assert not result["warnings"]


def test_audit_python_library_reports_missing_deployment():
    with TemporaryDirectory() as directory:
        root = Path(directory) / "library"
        initialize(root, "library", profile="python-library")
        result = audit(root)
        assert "ansible-install" in result["missing"]
