"""Portable staging-to-canonical assembly for the fan-out phases.

The methodology's fan-out phases dispatch one subagent per unit, each writing to
`<engagement>/_staging/<phase>/<unit>.md`. This module assembles the canonical
artifacts from those staging files: it splits/renumbers provisional ids, builds
`_index.md` tables, promotes files to their canonical folder, concatenates in a
fixed order, and clears staging.

Stdlib only — so it runs in any Python sandbox, including Claude.ai's Python-only
code tool — and it computes **no numbers**: all arithmetic stays in the engine.
Ordering is always canonical (sorted filenames, or an explicit ``order``), never
subagent completion order, so output is byte-identical regardless of dispatch
timing.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

# An extraction header:  <!-- index: id=OPP-001 type=Automation ... -->
_INDEX_RE = re.compile(r"<!--\s*index:(.*?)-->", re.DOTALL)
_KV_RE = re.compile(r"(\w+)=([^\s>]*)")
# A provisional heading:  ## TEMP-<token>   (token may contain hyphens/digits)
_TEMP_HEADING_RE = re.compile(r"^##\s+(TEMP-\S+)", re.MULTILINE)


def collect_staged(staging_dir) -> list[Path]:
    """Return staged files in deterministic (sorted) order; ``[]`` if absent."""
    d = Path(staging_dir)
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_file())


def _header_fields(text: str) -> dict[str, str]:
    m = _INDEX_RE.search(text)
    return dict(_KV_RE.findall(m.group(1))) if m else {}


def _render_table(columns, rows) -> str:
    """``columns``: list of ``(Header, key)``; ``rows``: list of dicts."""
    headers = [h for h, _ in columns]
    keys = [k for _, k in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(k, "") for k in keys) + " |")
    return "\n".join(lines) + "\n"


def renumber_sequential(files, dest_dir, prefix, *, order=None) -> list[str]:
    """Split staged files containing ``## TEMP-<token>`` blocks into one
    canonical ``<dest_dir>/<PREFIX>-NNN.md`` per block.

    Blocks are numbered sequentially across ``files`` (reordered to ``order`` —
    a list of file names — when given, else taken as passed). Each block's own
    provisional ``TEMP-`` token is rewritten to its final ``<PREFIX>-NNN`` id
    throughout that block (heading + body), matching the legacy awk. Text before
    the first heading in a file is discarded (the awk emits nothing while no
    output file is open). Returns the assigned ids in order.
    """
    paths = [Path(f) for f in files]
    if order is not None:
        rank = {name: i for i, name in enumerate(order)}
        paths = sorted(paths, key=lambda p: (rank.get(p.name, len(rank)), p.name))
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    assigned: list[str] = []
    n = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        matches = list(_TEMP_HEADING_RE.finditer(text))
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[start:end]
            temp_id = m.group(1)
            n += 1
            final_id = f"{prefix}-{n:03d}"
            block = block.replace(temp_id, final_id)
            (dest / f"{final_id}.md").write_text(block, encoding="utf-8")
            assigned.append(final_id)
    return assigned


def index_from_headers(files, dest_index, columns) -> int:
    """Rebuild ``_index.md`` at ``dest_index`` from each file's
    ``<!-- index: key=val ... -->`` header. ``columns`` is an ordered list of
    ``(Header, key)``; a missing key yields an empty cell. Returns row count."""
    rows = [_header_fields(Path(f).read_text(encoding="utf-8")) for f in files]
    Path(dest_index).write_text(_render_table(columns, rows), encoding="utf-8")
    return len(rows)


def index_from_fields(files, dest_index, columns, extract) -> int:
    """Like :func:`index_from_headers`, but field values come from
    ``extract(path) -> dict`` — for phases whose source of truth is the
    assembled file body, not an extraction header (Phase 4). Returns row count."""
    rows = [extract(Path(f)) for f in files]
    Path(dest_index).write_text(_render_table(columns, rows), encoding="utf-8")
    return len(rows)


def promote(staging_dir, dest_dir, *, pattern="*.md") -> list[Path]:
    """Move per-unit staged files matching ``pattern`` to ``dest_dir``. Returns
    the moved destination paths, sorted. Missing staging dir → ``[]``."""
    src = Path(staging_dir)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    moved: list[Path] = []
    sources = sorted(src.glob(pattern)) if src.is_dir() else []
    for p in sources:
        target = dest / p.name
        shutil.move(str(p), str(target))
        moved.append(target)
    return moved


def concat_ordered(files, dest_file, order, *, sep="\n") -> Path:
    """Concatenate ``files`` into ``dest_file`` in ``order`` (a list of unit ids
    matched against file stems). Files whose stem is not in ``order`` are
    appended last in sorted-stem order. Format-agnostic (md or html). Returns
    ``dest_file``."""
    paths = [Path(f) for f in files]
    rank = {uid: i for i, uid in enumerate(order)}
    ordered = sorted(paths, key=lambda p: (rank.get(p.stem, len(rank)), p.name))
    body = sep.join(p.read_text(encoding="utf-8") for p in ordered)
    out = Path(dest_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    return out


def cleanup(staging_dir) -> None:
    """Remove the staging tree (idempotent; no error if absent)."""
    shutil.rmtree(Path(staging_dir), ignore_errors=True)
