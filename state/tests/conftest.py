import pytest


@pytest.fixture
def engagement(tmp_path):
    """Return a builder that creates files inside a temp engagement folder.

    Usage:
        path = engagement("scope.md", "context.md")        # empty files
        path = engagement(**{"model/scores.json": "[]"})   # file with content
    """
    root = tmp_path / "acme-engagement"
    root.mkdir()

    def build(*empty_files, **files_with_content):
        for rel in empty_files:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("")
        for rel, content in files_with_content.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        return root

    return build
