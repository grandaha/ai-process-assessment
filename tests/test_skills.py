"""Every Phase Map skill ID resolves to a well-formed SKILL.md; no orphans."""

# Skills intentionally absent from the Phase Map:
#   using-methodology     — the keystone (carries the map itself)
#   running-sample-engagement — meta entry point for the bundled demo
#   generating-sample-intake  — demo-support: synthesizes sample intake files
#   building-checkpoint   — cross-cutting stakeholder validation checkpoint (interim)
ALLOWLIST_NON_PHASE = {
    "ai-process-assessment:using-methodology",
    "ai-process-assessment:running-sample-engagement",
    "ai-process-assessment:generating-sample-intake",
    "ai-process-assessment:building-checkpoint",
    "ai-process-assessment:conducting-engagement",
    "ai-process-assessment:generate-artifact",
}


def test_every_phase_skill_id_has_a_skill_file(methodology):
    for p in methodology.phases:
        assert p.skill_id in methodology.skills, \
            f"Phase {p.phase} skill ID has no skills/*/SKILL.md: {p.skill_id}"


def test_every_skill_has_name_frontmatter(methodology):
    for skill in methodology.skills.values():
        assert skill.skill_id, f"missing frontmatter name: {skill.path}"
        assert skill.skill_id.startswith("ai-process-assessment:"), skill.path


def test_every_skill_has_description_frontmatter(methodology):
    for skill in methodology.skills.values():
        assert skill.description, f"missing frontmatter description: {skill.path}"


def test_skill_name_matches_directory(methodology):
    for skill in methodology.skills.values():
        assert skill.skill_id == f"ai-process-assessment:{skill.dir_name}", \
            f"name/dir mismatch: {skill.skill_id} in {skill.path}"


def test_no_orphan_skills(methodology):
    phase_ids = {p.skill_id for p in methodology.phases}
    allowed = phase_ids | ALLOWLIST_NON_PHASE
    orphans = [sid for sid in methodology.skills if sid not in allowed]
    assert not orphans, f"skills not in Phase Map or allow-list: {orphans}"


def test_skill_count(methodology):
    # 14 phase skills + 6 allow-listed non-phase skills (incl. the conductor).
    assert len(methodology.skills) == 20
