from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .application.runner import run
from .config import load as load_config
from .errors import TripwireError
from .state import load as load_state
from .state import write_atomic

DEFAULT_CONFIG = Path("config/monitors.json")
DEFAULT_STATE = Path("state.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Configuration-driven change detection and notifications.")
    parser.add_argument("command", choices=("run", "validate"), nargs="?", default="run")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.command == "validate":
            print(f"VALID {args.config}")
            return 0
        state = load_state(args.state)
        result = run(config, state, args.dry_run)
        if not args.dry_run:
            write_atomic(args.state, state)
        return result
    except TripwireError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
