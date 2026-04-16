from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.models import Technique
from app.seed import CORE_TECHNIQUE_CODES, EXTENDED_TECHNIQUE_CODES
from app.services.attack_import import iter_enterprise_attack_techniques_from_bundle


DEFAULT_ATTACK_URL = (
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/"
    "enterprise-attack/enterprise-attack.json"
)


def import_enterprise_attack(database_path: Path, bundle_url: str = DEFAULT_ATTACK_URL) -> tuple[int, int]:
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db: Session = session_factory()
    try:
        response = httpx.get(bundle_url, timeout=60.0, follow_redirects=True)
        response.raise_for_status()
        bundle = response.json()
        imported_rows = iter_enterprise_attack_techniques_from_bundle(
            bundle,
            core_codes=CORE_TECHNIQUE_CODES,
            extended_codes=EXTENDED_TECHNIQUE_CODES,
        )

        existing_by_code = {
            row.code: row
            for row in db.scalars(select(Technique)).all()
        }
        created = 0
        updated = 0
        for payload in imported_rows:
            existing = existing_by_code.get(str(payload["code"]))
            if existing is None:
                db.add(Technique(**payload))
                created += 1
                continue

            for field, value in payload.items():
                setattr(existing, field, value)
            updated += 1

        db.commit()
        return created, updated
    finally:
        db.close()
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Import MITRE ATT&CK Enterprise techniques into DefenseGraph.")
    parser.add_argument(
        "--db",
        default=str(BACKEND_DIR / "defensegraph.db"),
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_ATTACK_URL,
        help="Remote ATT&CK Enterprise STIX bundle URL.",
    )
    args = parser.parse_args()

    database_path = Path(args.db).resolve()
    created, updated = import_enterprise_attack(database_path, args.url)
    print(f"Imported ATT&CK Enterprise techniques into {database_path}")
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
