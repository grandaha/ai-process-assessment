import pytest

from state.improvement_log import Escape, prepend_entry, render_entry

ESC = Escape(
    date="2026-06-24", phase="5", skill="identifying-opportunities",
    engagement="acme / round 1",
    shortcut="This step doesn't look like an AI candidate — let's skip it.",
    would_produce="A process dropped before its chain potential was evaluated.",
    why_uncaught="The step-by-step comparative-advantage row should have caught it.",
    reframe="Evaluate every step in the context of its neighbors, not in isolation.",
)


def test_render_entry_has_format_fields():
    out = render_entry(ESC)
    assert "### [2026-06-24] Phase 5 — identifying-opportunities" in out
    assert "**Engagement/Round:** acme / round 1" in out
    assert "**Shortcut taken:** This step doesn't look like an AI candidate" in out
    assert "**What it produced:** A process dropped" in out
    assert "**Why the table didn't catch it:**" in out
    # the proposed reframe row
    assert "| Rationalization / Shortcut | Correct Reframe |" in out
    assert "Evaluate every step in the context of its neighbors" in out
    # GREEN/REFACTOR fields are pending for an auto-RED entry
    assert "**Keystone updated:** pending" in out
    assert "**Checklist/gate step updated:** pending" in out


def test_render_entry_reframe_pending_when_no_row():
    esc = Escape(date="2026-06-24", phase="n/a", skill="conductor",
                 engagement="n/a", shortcut="some novel shortcut",
                 would_produce="x", why_uncaught="no row existed", reframe="pending")
    out = render_entry(esc)
    assert "| some novel shortcut | pending |" in out


def test_prepend_scaffolds_absent_file(tmp_path):
    log = tmp_path / "improvement-log.md"
    prepend_entry(log, ESC)
    text = log.read_text()
    assert text.startswith("# Improvement Log")
    assert "## Entries" in text
    assert "### [2026-06-24] Phase 5 — identifying-opportunities" in text


def test_prepend_newest_first_and_preserves_prior(tmp_path):
    log = tmp_path / "improvement-log.md"
    first = Escape(date="2026-06-01", phase="4", skill="discovering-processes",
                   engagement="e1", shortcut="FIRST-SHORTCUT", would_produce="x",
                   why_uncaught="y", reframe="z")
    prepend_entry(log, first)
    prepend_entry(log, ESC)  # newer
    text = log.read_text()
    # newest appears before the older one
    assert text.index("identifying-opportunities") < text.index("discovering-processes")
    # the older entry is preserved verbatim
    assert "FIRST-SHORTCUT" in text


def test_prepend_preserves_existing_yes_no_entry(tmp_path):
    log = tmp_path / "improvement-log.md"
    log.write_text(
        "# Improvement Log\n\n## Entries\n\n"
        "### [2026-05-01] Phase 4 — discovering-processes\n\n"
        "**Keystone updated:** no\n**Checklist/gate step updated:** no\n"
    )
    prepend_entry(log, ESC)
    text = log.read_text()
    # existing yes/no entry untouched
    assert "**Keystone updated:** no" in text
    # new entry present and ahead of it
    assert text.index("identifying-opportunities") < text.index("discovering-processes")


def test_prepend_raises_without_entries_header(tmp_path):
    log = tmp_path / "improvement-log.md"
    log.write_text("# Some other log\n\nfreeform notes, no Entries header\n")
    with pytest.raises(ValueError):
        prepend_entry(log, ESC)


def test_prepend_is_deterministic(tmp_path):
    log1 = tmp_path / "a.md"
    log2 = tmp_path / "b.md"
    prepend_entry(log1, ESC)
    prepend_entry(log2, ESC)
    assert log1.read_text() == log2.read_text()
