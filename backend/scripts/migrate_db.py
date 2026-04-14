from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.migration import migrate_legacy_database


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a previous DefenseGraph SQLite database in place.")
    parser.add_argument(
        "--db",
        default=str(BACKEND_DIR / "defensegraph.db"),
        help="Path to the SQLite database file.",
    )
    args = parser.parse_args()

    database_path = Path(args.db).resolve()
    backup_path = migrate_legacy_database(database_path)

    if backup_path is None:
        print(f"No migration required for {database_path}")
        return 0

    print(f"Migrated database: {database_path}")
    print(f"Backup created at: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
