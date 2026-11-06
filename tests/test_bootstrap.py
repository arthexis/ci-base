from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import initialize


def test_python_starter():
    with TemporaryDirectory() as temp:
        target = Path(temp) / "my-app"
        initialize(target, "my-app", ansible=False)
        assert (target / "pyproject.toml").exists()
        assert (target / ".github/workflows/quality.yml").exists()
        assert not (target / "deploy.sh").exists()
        assert not (target / "templates").exists()


def test_ansible_starter():
    with TemporaryDirectory() as temp:
        target = Path(temp) / "my-app"
        initialize(target, "my-app", ansible=True)
        assert (target / "deploy.sh").stat().st_mode & 0o111
        assert (target / "ansible/playbooks/install.yml").exists()
        assert (target / ".github/workflows/ansible.yml").exists()
        assert "my-app" in (target / "ansible/roles/app/defaults/main.yml").read_text()
        assert not (target / "templates").exists()
