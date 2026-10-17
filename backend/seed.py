"""Add missing Samsung Electronics close prices without overwriting edits."""

import argparse
import csv
from pathlib import Path

from dotenv import load_dotenv

from app.store import db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Validate the CSV without writing to Firestore")
    args = parser.parse_args()
    load_dotenv()
    path = Path(__file__).parent / "data" / "samsung_005930_daily.csv"
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    dates = [row["date"] for row in rows]
    if len(rows) < 100 or len(dates) != len(set(dates)):
        raise SystemExit("At least 100 unique dates are required")
    if args.dry_run:
        print(f"DRY RUN: {len(rows)} records, {dates[0]} through {dates[-1]}")
        return

    client = db()
    collection = client.collection("data")
    existing = {doc.id for doc in collection.stream()}
    missing = [row for row in rows if row["date"] not in existing]
    for start in range(0, len(missing), 400):
        batch = client.batch()
        for row in missing[start:start + 400]:
            batch.set(collection.document(row["date"]), {
                "date": row["date"], "value": float(row["value"]), "memo": row["memo"]
            })
        batch.commit()
    print(f"Added {len(missing)} records; kept {len(rows) - len(missing)} existing dates")


if __name__ == "__main__":
    main()
