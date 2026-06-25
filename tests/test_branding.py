"""OSL branding guards: vendored assets exist and are on-brand."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OSL = REPO / "assets" / "osl"
BRAND = OSL / "brand.css"
LOGO = OSL / "logo-lockup.svg"


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
