"""OSL branding guards: vendored assets exist and are on-brand."""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
OSL = REPO / "assets" / "osl"
BRAND = OSL / "brand.css"
LOGO = OSL / "logo-lockup.svg"
COMPONENTS = OSL / "components.css"
DELIVERABLE_SKILL = REPO / "skills" / "building-deliverable" / "SKILL.md"


def test_brand_assets_exist():
    assert BRAND.exists(), "assets/osl/brand.css missing"
    assert LOGO.exists(), "assets/osl/logo-lockup.svg missing"
    assert (OSL / "SOURCE.md").exists(), "assets/osl/SOURCE.md missing"


def test_brand_css_is_on_brand():
    css = BRAND.read_text(encoding="utf-8")
    assert "--blue-500: #1B75BC" in css, "OSL primary blue token missing"
    assert "--orange-500: #E06030" in css, "OSL accent orange token missing"
    assert "DM Sans" in css and "DM Mono" in css, "OSL fonts missing"
    assert "fonts.googleapis.com" in css, "webfont @import missing"


def test_logo_is_svg():
    svg = LOGO.read_text(encoding="utf-8").strip()
    assert svg.startswith("<svg") or svg.startswith("<?xml"), "logo not SVG"
    assert "one step labs" in svg.lower(), "logo lockup text missing"


def _contract_classes() -> set[str]:
    """Class tokens named in building-deliverable's 'Required CSS components' section."""
    text = DELIVERABLE_SKILL.read_text(encoding="utf-8")
    start = text.index("## Required CSS components")
    end = text.find("\n## ", start + 1)
    section = text[start: end if end != -1 else len(text)]
    classes = set()
    for span in re.findall(r"`([^`]+)`", section):          # inline-code spans only
        for cls in re.findall(r"\.[a-zA-Z][\w-]*", span):    # .class tokens within them
            classes.add(cls)
    return classes


def test_components_exist():
    assert COMPONENTS.exists(), "assets/osl/components.css missing"


def test_every_contract_class_is_defined():
    css = COMPONENTS.read_text(encoding="utf-8")
    missing = sorted(c for c in _contract_classes() if c not in css)
    assert not missing, f"contract classes absent from components.css: {missing}"


def test_components_use_tokens_not_raw_hex():
    css = COMPONENTS.read_text(encoding="utf-8")
    # No raw 3/6-digit hex colors — components reference brand tokens via var().
    hexes = re.findall(r"#[0-9A-Fa-f]{3,6}\b", css)
    assert not hexes, f"components.css must use var(--token), found raw hex: {hexes}"
    assert "var(--blue-500)" in css, "components.css should consume OSL tokens"
