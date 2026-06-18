from cockpit.overrides import parse_overrides, reconcile
from cockpit.state import read_state


REAL = (
    "| Override | Reason | Authorized by |\n"
    "|---|---|---|\n"
    "| Skip context mapping (context.md) | reuse from prior engagement | Dana Lee |\n"
)
PLACEHOLDER = (
    "| Override | Reason | Authorized by |\n"
    "|---|---|---|\n"
    "| <e.g., Skip context mapping> | <e.g., same client> | <name> |\n"
)


def test_parses_real_override_to_output_path():
    assert parse_overrides(REAL) == {"context.md"}


def test_ignores_placeholder_template_row():
    assert parse_overrides(PLACEHOLDER) == set()


def test_ignores_row_missing_reason_or_authorizer():
    text = (
        "| Override | Reason | Authorized by |\n"
        "|---|---|---|\n"
        "| Skip context.md |  |  |\n"
    )
    assert parse_overrides(text) == set()


def test_matches_by_bare_skill_name():
    text = (
        "| Override | Reason | Authorized by |\n"
        "|---|---|---|\n"
        "| Skip mapping-context | stable | Dana |\n"
    )
    assert parse_overrides(text) == {"context.md"}


def test_reconcile_unblocks_phase_after_overridden_predecessor(engagement):
    root = engagement("scope.md")  # phase 1 done, 2 available, 3 blocked
    snap = reconcile(read_state(root), {"context.md"})
    by_id = {p["id"]: p for p in snap["phases"]}
    assert by_id["2"]["status"] == "overridden"
    assert by_id["3"]["status"] == "available"
    assert by_id["3"]["blocked_reason"] is None
