from __future__ import annotations

import argparse
from pathlib import Path

from scheme_engine.core.pipeline import run


def main():
    parser = argparse.ArgumentParser(description="Scheme Intelligence Engine scraper")
    parser.add_argument("--seeds", default="scheme_engine/config/portals_full.json")
    parser.add_argument("--settings", default="scheme_engine/config/settings.json")
    parser.add_argument("--db", default="data/schemes.db")
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--depth", type=int, default=1)
    args = parser.parse_args()

    Path("data").mkdir(exist_ok=True)
    run(
        seeds_path=args.seeds,
        settings_path=args.settings,
        db_path=args.db,
        limit=args.limit,
        depth=args.depth,
    )


if __name__ == "__main__":
    main()
