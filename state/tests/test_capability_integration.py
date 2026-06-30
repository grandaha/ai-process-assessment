from state import capability as cap
from state import process_review as pr

# A full new-format process: action-only Steps + a Step capability table (no colors authored).
PROC = """## PROC-001 — Client Onboarding

**Trigger:** A deal closes.

### Process Map

**Steps:**
1. Re-keys client details into Teamwork
2. Builds the task list from the Notion checklist
3. Waits for the client to provide materials
4. Reviews assets and decides whether to proceed

**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data, rule-based | both systems API-available (tech-inventory) |
| 2 | structured-data, templated | Notion checklist is templated |
| 3 | external-dependency | operator: we wait on the client |
| 4 | structured-data, human-judgment | operator: I decide if there is enough |

**Actors:** PM team; HubSpot; Teamwork.
"""

def test_colors_and_chains_computed():
    assert cap.step_colors(PROC) == {1: "Green", 2: "Green", 3: "Red", 4: "Yellow"}
    assert cap.compute_chains(cap.step_colors(PROC)) == [(1, 2)]

def test_validate_clean():
    assert cap.validate(PROC) == []

def test_owner_doc_excludes_capability_table():
    blocks = pr.build_blocks(PROC)
    text = " ".join(b.get("text", "") + " ".join(b.get("items", [])) for b in blocks)
    assert "Step capability" not in text            # assessor-only
    for a in ("structured-data", "external-dependency", "human-judgment"):
        assert a not in text                        # no attributes leak into the owner doc
    # the clean step actions DO render
    assert any(b["type"] == "numbered_list" for b in blocks)
    steps = next(b for b in blocks if b["type"] == "numbered_list")
    assert steps["items"][0] == "Re-keys client details into Teamwork"
