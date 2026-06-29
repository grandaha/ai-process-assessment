# tests/test_doc_rendering.py — renderer-output tests (#148). Run with python3.13.
import json
import zipfile

from state import docx
from state import checkpoint_doc as cd


def _types(blocks):
    return [b["type"] for b in blocks]


def test_bullet_list_factory():
    b = docx.bullet_list(["a", "b"])
    assert b == {"type": "bullet_list", "items": ["a", "b"]}


def test_bullet_list_renders_with_bullet_glyph(tmp_path):
    out = tmp_path / "d.docx"
    docx.build_docx([docx.bullet_list(["first", "second"])], str(out))
    with zipfile.ZipFile(out) as z:
        body = z.read("word/document.xml").decode("utf-8")
    assert "• first" in body
    assert "• second" in body


def test_blocks_from_markdown_groups_consecutive_bullets():
    blocks = cd.blocks_from_markdown("- one\n- two\n- three")
    assert _types(blocks) == ["bullet_list"]
    assert blocks[0]["items"] == ["one", "two", "three"]


def test_blocks_from_markdown_groups_consecutive_numbers():
    blocks = cd.blocks_from_markdown("1. one\n2. two")
    assert _types(blocks) == ["numbered_list"]
    assert blocks[0]["items"] == ["one", "two"]


def test_blocks_from_markdown_strips_bold_in_list_items():
    blocks = cd.blocks_from_markdown("- a **bold** item")
    assert blocks[0]["items"] == ["a bold item"]


def test_blocks_from_markdown_preserves_interleaved_prose_and_table():
    md = "Intro line\n\n- b1\n- b2\n\n| H1 | H2 |\n|---|---|\n| x | y |"
    blocks = cd.blocks_from_markdown(md)
    t = _types(blocks)
    assert t == ["paragraph", "bullet_list", "table"]
    assert blocks[1]["items"] == ["b1", "b2"]
    assert blocks[2]["headers"] == ["H1", "H2"]


def test_blocks_from_markdown_switches_bullet_to_number_into_two_lists():
    blocks = cd.blocks_from_markdown("- a\n1. b")
    assert _types(blocks) == ["bullet_list", "numbered_list"]


from state import process_review as pr

PROC = """## PROC-001 — Client Onboarding & Project Setup
<!-- index: baseline=Ready -->

**Trigger:** HubSpot deal marked "Closed Won"; Zapier creates a Teamwork project.

### Process Map

**Steps:**
1. PM receives Slack notification — **Green** (fully automated trigger; no human input)
2. PM re-keys client details into Teamwork — **Green** (structured data transfer)
3. PM waits for client materials — **Red** (external dependency on client)

**Actors:** Tyler Brooks / PM team; HubSpot; Zapier; Teamwork.

**Decision points:**
- Whether to proceed to kickoff with partial assets (judgment call)
- Whether scope gaps require a change order before work begins

**Exceptions:**
- Client never responds to asset requests (~5% of projects)
- Client-provided credentials do not work (~15% of projects)

**Upstream / downstream:**
- Upstream: HubSpot deal closure; no pre-sale asset checklist
- Downstream: PROC-003 launches as a parallel subprocess

**Conflicts:**
- **Conflict A:** internal assessor analysis that must never render.

**Chain scan:**
- Steps 1-2 form a Green chain — internal analysis, excluded.

**Challenge hypothesis:** Internal redesign analysis, excluded.

### Baselines

| Field | Value | Source | Confidence |
|---|---|---|---|
| Volume | 6-8 projects/month | Teamwork log | Medium |
| Cycle time | Median 18 days | Tyler's sheet | Medium-High |
"""


def test_field_body_captures_all_decision_points():
    body = pr._field_body(PROC, "Decision points")
    assert body.count("- ") == 2
    assert "partial assets" in body
    assert "change order" in body


def test_field_body_captures_all_exceptions():
    body = pr._field_body(PROC, "Exceptions")
    assert "never responds" in body
    assert "credentials do not work" in body


def test_field_body_single_line_trigger():
    body = pr._field_body(PROC, "Trigger")
    assert body.startswith("HubSpot deal")
    assert "Closed Won" in body


def test_steps_are_clean_actions():
    steps = pr._steps(PROC)
    assert len(steps) == 3
    joined = " ".join(steps)
    for marker in ("Green", "Yellow", "Red", "**", "—", "(", "automated trigger"):
        assert marker not in joined, f"leaked {marker!r} into steps"
    assert steps[0] == "PM receives Slack notification"


def test_build_blocks_renders_both_decision_points_as_bullets():
    blocks = pr.build_blocks(PROC)
    # find the bullet_list that follows the "Decision points" heading
    idx = next(i for i, b in enumerate(blocks)
               if b["type"] == "heading" and b["text"] == "Decision points")
    lst = blocks[idx + 1]
    assert lst["type"] == "bullet_list"
    assert len(lst["items"]) == 2


def test_build_blocks_excludes_internal_sections():
    blocks = pr.build_blocks(PROC)
    text = " ".join(b.get("text", "") + " ".join(b.get("items", [])) for b in blocks)
    assert "Conflict A" not in text
    assert "Chain scan" not in text
    assert "Challenge hypothesis" not in text
    assert "redesign analysis" not in text


def test_build_blocks_keeps_baselines_and_signoff():
    blocks = pr.build_blocks(PROC)
    headings = [b["text"] for b in blocks if b["type"] == "heading"]
    assert "Baseline figures (for context)" in headings
    assert "Sign-off" in headings
    assert any(b["type"] == "table" for b in blocks)


def test_build_blocks_no_leaked_markers_anywhere():
    blocks = pr.build_blocks(PROC)
    for b in blocks:
        for s in [b.get("text", "")] + b.get("items", []):
            assert "**" not in s
            assert " → " not in s


# --- baseline checkpoint: real list-of-objects shape (#149) ---
def _mk_engagement(tmp_path):
    (tmp_path / "processes").mkdir()
    (tmp_path / "model").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| Process | Name | Baseline |\n|---|---|---|\n"
        "| PROC-001 | Client Onboarding | Ready |\n"
        "| PROC-002 | Change Orders | Ready |\n",
        encoding="utf-8")
    # The engine input shape: a LIST of per-process objects (NOT a dict keyed by pid).
    (tmp_path / "model" / "baselines.json").write_text(json.dumps([
        {"process_id": "PROC-001", "volume": 7, "cycle_time_median": 18,
         "cycle_time_p90": 34, "error_rate": 0.20, "fte": 0.197, "source": "x"},
        {"process_id": "PROC-002", "volume": 19, "cycle_time_median": 3,
         "cycle_time_p90": 9, "error_rate": 0.35, "fte": 0.297, "source": "y"},
    ]), encoding="utf-8")
    return tmp_path


def test_build_baseline_does_not_crash_on_list_shape(tmp_path):
    blocks = cd._build_baseline(_mk_engagement(tmp_path))
    assert any(b["type"] == "table" for b in blocks)


def test_build_baseline_populates_real_fields(tmp_path):
    blocks = cd._build_baseline(_mk_engagement(tmp_path))
    table = next(b for b in blocks if b["type"] == "table")
    row = next(r for r in table["rows"] if r[0] == "PROC-001")
    proc, name, volume, cycle, err, fte = row
    assert name == "Client Onboarding"
    assert str(volume) == "7"
    assert "18" in str(cycle) and "34" in str(cycle)   # median + P90
    assert err == "20%"
    assert fte == "0.20"
    assert "PENDING" not in [str(c) for c in row]


def test_build_baseline_pending_for_missing_process(tmp_path):
    root = _mk_engagement(tmp_path)
    # add a third Ready process with no baseline entry -> all metrics PENDING, no crash
    (root / "processes" / "_index.md").write_text(
        "| Process | Name | Baseline |\n|---|---|---|\n"
        "| PROC-001 | Client Onboarding | Ready |\n"
        "| PROC-003 | Asset Collection | Ready |\n",
        encoding="utf-8")
    blocks = cd._build_baseline(root)
    table = next(b for b in blocks if b["type"] == "table")
    row = next(r for r in table["rows"] if r[0] == "PROC-003")
    assert row[1] == "Asset Collection"
    assert row[2] == "PENDING"          # volume
    assert row[3] == "PENDING"          # cycle time
    assert row[4] == "PENDING"          # error rate
    assert row[5] == "PENDING"          # fte
