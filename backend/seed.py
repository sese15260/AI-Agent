"""Load the checked-in Samsung Electronics close series into Firestore."""
import csv
from pathlib import Path

from dotenv import load_dotenv
from app.store import db

load_dotenv()
path = Path(__file__).parent / "data" / "samsung_005930_daily.csv"
with path.open(encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))
if len(rows) < 100:
    raise SystemExit("At least 100 records are required")
batch = db().batch()
collection = db().collection("data")
for row in rows:
    batch.set(collection.document(row["date"]), {"date": row["date"], "value": float(row["value"]), "memo": row["memo"]})
batch.commit()
print(f"Seeded {len(rows)} records, {rows[0]['date']} through {rows[-1]['date']}")
