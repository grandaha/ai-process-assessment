"""plugin.json is valid + semver, and its version matches INSTALL.md.

Version invariant is INTERNAL CONSISTENCY (plugin.json <-> INSTALL.md), not
tag-equality — a bump legitimately precedes its git tag during release prep.
The tag comparison below is an optional, skip-on-absence soft check.
"""
import json
import re
import subprocess

from methodology_model import REPO_ROOT

import pytest

PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
INSTALL_MD = REPO_ROOT / "INSTALL.md"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CHANGELOG_MD = REPO_ROOT / "CHANGELOG.md"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def _plugin_version() -> str:
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]


def test_plugin_json_is_valid_json_with_version():
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    assert "version" in data
    assert data.get("name") == "ai-process-assessment"


def test_plugin_version_is_semver():
    version = _plugin_version()
    assert SEMVER_RE.match(version), f"not valid semver: {version}"


def test_install_md_version_matches_plugin_json():
    version = _plugin_version()
    install = INSTALL_MD.read_text(encoding="utf-8")
    m = re.search(r'"version":\s*"([^"]+)"', install)
    assert m, "no version string found in INSTALL.md"
    assert m.group(1) == version, \
        f"INSTALL.md version {m.group(1)} != plugin.json version {version}"


def _semver_tuple(v: str) -> tuple[int, int, int]:
    core = v.lstrip("v").split("-")[0].split("+")[0]
    parts = core.split(".")
    return tuple(int(x) for x in (parts + ["0", "0", "0"])[:3])


def test_version_not_behind_latest_tag():
    # Optional soft check; skips cleanly when git/tags are unavailable.
    try:
        out = subprocess.run(
            ["git", "tag", "--list", "v*"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("git unavailable")
    tags = [t for t in out.split() if SEMVER_RE.match(t.lstrip("v"))]
    if not tags:
        pytest.skip("no semver tags present")
    latest = max(tags, key=_semver_tuple)
    assert _semver_tuple(_plugin_version()) >= _semver_tuple(latest), \
        f"plugin.json version {_plugin_version()} is behind latest tag {latest}"


def test_marketplace_json_version_matches_plugin_json():
    version = _plugin_version()
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugins = data.get("plugins", [])
    match = next((p for p in plugins if p.get("name") == "ai-process-assessment"), None)
    assert match is not None, "ai-process-assessment entry missing from marketplace.json"
    assert match.get("version") == version, \
        f"marketplace.json version {match.get('version')} != plugin.json version {version}"


def test_changelog_has_section_for_current_version():
    version = _plugin_version()
    changelog = CHANGELOG_MD.read_text(encoding="utf-8")
    assert re.search(r"^## \[" + re.escape(version) + r"\]", changelog, re.MULTILINE), \
        f"CHANGELOG.md has no '## [{version}]' section"
