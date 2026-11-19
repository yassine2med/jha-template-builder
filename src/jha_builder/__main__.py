"""Command line entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import load_job, render


def main(argv: list[str] | None = None) -> int:
    """Print the JHA sheet for a job file."""
    parser = argparse.ArgumentParser(prog="jha_builder")
    parser.add_argument("job_file", type=Path)
    args = parser.parse_args(argv)
    try:
        title, hazards = load_job(args.job_file)
    except (OSError, ValueError) as exc:  # JSONDecodeError is a ValueError
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(render(title, hazards))
    return 0


if __name__ == "__main__":
    sys.exit(main())
