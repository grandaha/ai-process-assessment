"""Chain-to-next-skill links resolve and form one connected phase path."""

ENTRY_SKILL = "ai-process-assessment:scoping-engagement"
TERMINAL_SKILL = "ai-process-assessment:building-deliverable"


def test_every_chain_target_resolves(methodology):
    for skill in methodology.skills.values():
        if skill.chain_target is None:
            continue
        assert skill.chain_target in methodology.skills, \
            f"{skill.skill_id} chains to unknown skill: {skill.chain_target}"


def test_chain_forms_one_connected_path(methodology):
    # Walk from the Phase 1 entry skill following chain_target until terminal,
    # detecting cycles. The walk must cover every phase skill and end at Phase 11.
    visited: list[str] = []
    seen: set[str] = set()
    current = ENTRY_SKILL
    while current is not None and current not in seen:
        seen.add(current)
        visited.append(current)
        skill = methodology.skills.get(current)
        if skill is None:
            break
        current = skill.chain_target

    assert visited[-1] == TERMINAL_SKILL, \
        f"chain did not terminate at Phase 11: ended at {visited[-1]}"

    phase_ids = {p.skill_id for p in methodology.phases}
    missing = phase_ids - set(visited)
    assert not missing, f"chain does not cover these phase skills: {sorted(missing)}"


def test_terminal_skill_has_no_chain_target(methodology):
    assert methodology.skills[TERMINAL_SKILL].chain_target is None
