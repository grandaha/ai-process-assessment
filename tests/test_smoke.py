"""Smoke test: the methodology model parses and is non-empty."""


def test_model_loads(methodology):
    assert methodology.phases, "no phase rows parsed from the keystone Phase Map"
    assert methodology.skills, "no skills loaded"
    assert methodology.agents, "no agents loaded"
    assert methodology.convention_files, "no Engagement Folder Convention files parsed"
