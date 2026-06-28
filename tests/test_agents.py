"""Agents are well-formed; every agent referenced by a skill resolves."""
import re

# Backticked bare-identifier tokens captured by the dispatch-phrasing patterns
# below that are NOT agents. Empty today; populate (with a comment) only if
# test_referenced_agents_resolve surfaces a false positive during implementation.
NON_AGENT_TOKENS: set[str] = set()

# Agents referenced by no skill. Empty today — all 14 agents are referenced.
ORPHAN_AGENT_ALLOWLIST: set[str] = set()

# Phrasings that unambiguously introduce an agent. Each requires the ENTIRE
# backtick span to be a bare identifier (open-backtick + token + close-backtick),
# so file tokens like `process-map.md` or `_staging/phase6/OPP.md` never match.
_REF_PATTERNS = [
    re.compile(r"`([a-z][a-z0-9-]+)`\s+subagent"),          # "`name` subagent"
    re.compile(r"[Dd]ispatch[^`\n]{0,40}?`([a-z][a-z0-9-]+)`"),  # "dispatch ... `name`"
    re.compile(r"`([a-z][a-z0-9-]+)`\s*←"),                 # "`name` ← ..." (renderer arrow)
]


def test_every_agent_has_name_frontmatter(methodology):
    for agent in methodology.agents.values():
        assert agent.name, f"missing frontmatter name: {agent.path}"


def test_every_agent_has_description_frontmatter(methodology):
    for agent in methodology.agents.values():
        assert agent.description, f"missing frontmatter description: {agent.path}"


def test_agent_name_matches_filename(methodology):
    for agent in methodology.agents.values():
        assert agent.name == agent.path.stem, \
            f"name/filename mismatch: {agent.name} in {agent.path}"


def test_agent_count(methodology):
    # 14 = 17 prior agents - 3 section-renderer-checkpoint-* agents deleted in #131
    # (all checkpoints now route through the deterministic checkpoint_doc command).
    assert len(methodology.agents) == 14


def _referenced_agent_tokens(methodology) -> set[str]:
    """Tokens captured by the dispatch-phrasing patterns across all skill bodies,
    minus the NON_AGENT_TOKENS allow-list. Does NOT pre-filter by existence, so a
    dispatched-but-missing agent is caught by test_referenced_agents_resolve."""
    tokens: set[str] = set()
    for skill in methodology.skills.values():
        for pat in _REF_PATTERNS:
            for m in pat.finditer(skill.body):
                tok = m.group(1)
                if tok not in NON_AGENT_TOKENS:
                    tokens.add(tok)
    return tokens


def test_referenced_agents_resolve(methodology):
    # Every agent a skill dispatches must exist as a file in agents/.
    for tok in sorted(_referenced_agent_tokens(methodology)):
        assert tok in methodology.agents, (
            f"a skill dispatches an agent with no file: {tok!r} "
            f"(if this token is not an agent, add it to NON_AGENT_TOKENS)"
        )


def test_no_unexpected_orphan_agents(methodology):
    # Soft check: agents referenced by no skill at all. Allow-list is empty today.
    referenced: set[str] = set()
    for skill in methodology.skills.values():
        for name in methodology.agents:
            if name in skill.body:
                referenced.add(name)
    orphans = set(methodology.agents) - referenced - ORPHAN_AGENT_ALLOWLIST
    assert not orphans, f"agents referenced by no skill: {sorted(orphans)}"
