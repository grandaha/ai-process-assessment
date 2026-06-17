"""Launch the cockpit against an engagement folder.

Usage: python -m cockpit <engagement-folder> [--port 8765]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from cockpit.server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(prog="cockpit")
    parser.add_argument("engagement", type=Path, help="path to the engagement folder")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if not args.engagement.is_dir():
        parser.error(f"not a directory: {args.engagement}")

    app = create_app(args.engagement)
    print(f"Cockpit for '{args.engagement.name}' → http://127.0.0.1:{args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
