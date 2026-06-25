"""OSL branding guards: vendored assets exist and are on-brand."""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
OSL = REPO / "assets" / "osl"
BRAND = OSL / "brand.css"
LOGO = OSL / "logo-lockup.svg"
COMPONENTS = OSL / "components.css"
DELIVERABLE_SKILL = REPO / "skills" / "building-deliverable" / "SKILL.md"
CHECKPOINT_SKILL = REPO / "skills" / "building-checkpoint" / "SKILL.md"


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


def test_deliverable_skill_inlines_vendored_shell():
    text = DELIVERABLE_SKILL.read_text(encoding="utf-8")
    assert "assets/osl/brand.css" in text and "assets/osl/components.css" in text, \
        "building-deliverable must reference the vendored CSS"
    assert "assets/osl/logo-lockup.svg" in text, "masthead must inline the OSL logo"
    assert "verbatim" in text, "skill must say inline the shell verbatim"
    # The old model-authored-CSS instruction must be gone.
    assert "Section-renderer agents must not invent new CSS classes" not in text, \
        "the old model-authors-CSS wording must be removed, not left alongside the new"


def test_checkpoint_skill_inlines_vendored_shell():
    text = CHECKPOINT_SKILL.read_text(encoding="utf-8")
    assert "assets/osl/brand.css" in text and "assets/osl/components.css" in text, \
        "building-checkpoint must reference the vendored CSS"
    assert "assets/osl/logo-lockup.svg" in text, "checkpoint masthead must inline the OSL logo"
    assert "Generate the `<style>` from that documented design system" not in text, \
        "remove the model-generates-CSS instruction"


SAMPLE = REPO / "golden" / "pso-delivery" / "deliverable.html"


def test_sample_deliverable_is_osl_branded():
    html = SAMPLE.read_text(encoding="utf-8")
    assert "--blue-500: #1B75BC" in html, "sample not re-shelled with OSL brand tokens"
    assert "DM Sans" in html, "sample missing OSL fonts"
    assert 'class="brand-logo"' in html, "sample masthead missing inlined OSL logo"
    # Old model-invented palette token must be gone.
    assert "--slate-light:" not in html, "stale non-brand palette still present in sample"


def test_sample_has_no_dangling_css_vars():
    """Every var(--X) referenced in the sample must be defined in the vendored CSS
    (brand.css or components.css). Comments are stripped first so the components.css
    'var(--token)' doc comment is not counted as a reference."""
    import re
    html = SAMPLE.read_text(encoding="utf-8")
    no_comments = re.sub(r"/\*.*?\*/", "", html, flags=re.DOTALL)
    referenced = set(re.findall(r"var\(\s*(--[a-z0-9-]+)\s*\)", no_comments))
    defined_css = BRAND.read_text(encoding="utf-8") + COMPONENTS.read_text(encoding="utf-8")
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", defined_css))
    dangling = sorted(referenced - defined)
    assert not dangling, f"sample references undefined CSS vars: {dangling}"
