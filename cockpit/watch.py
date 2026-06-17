"""Async snapshot stream: yields a JSON snapshot now, then again on every change."""
from __future__ import annotations

import json
from pathlib import Path

from watchfiles import awatch

from cockpit.state import read_state


async def snapshot_events(engagement_dir):
    """Yield SSE 'data:' frames: the current snapshot, then one per filesystem change."""
    root = Path(engagement_dir).resolve()
    yield _frame(root)
    async for _changes in awatch(root):
        yield _frame(root)


def _frame(root: Path) -> str:
    return f"data: {json.dumps(read_state(root))}\n\n"
