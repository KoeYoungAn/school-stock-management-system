import os
import sys
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
from utils import record_movement

# In-memory DB
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=" * 60)
print("STOCK MOVEMENT DATE RANGE FILTERING TEST")
print("=" * 60)

# Setup test user
user = models.User(email="tester@example.com", role="Admin", full_name="Test Admin", password_hash="hash")
db.add(user)
db.commit()

# Setup test item
item = models.InventoryItem(
    item_code="ITM-TEST-001",
    item_name="Test Item",
    stock_quantity=100,
    category="Test"
)
db.add(item)
db.commit()

print(f"\n[PASS] Created test item: {item.item_code}")
print(f"  Initial stock: {item.stock_quantity}")

# Create movements on different dates
# We'll manually set the created_at timestamps to simulate movements on different days

base_date = datetime(2026, 6, 1, 10, 0, 0)  # June 1, 2026

movements_data = [
    {"date": base_date, "qty": 10, "type": "IN", "desc": "Day 1 - June 1"},
    {"date": base_date + timedelta(days=2), "qty": 5, "type": "OUT", "desc": "Day 3 - June 3"},
    {"date": base_date + timedelta(days=5), "qty": 15, "type": "IN", "desc": "Day 6 - June 6"},
    {"date": base_date + timedelta(days=7), "qty": 8, "type": "OUT", "desc": "Day 8 - June 8"},
    {"date": base_date + timedelta(days=10), "qty": 20, "type": "IN", "desc": "Day 11 - June 11"},
]

print(f"\n--- Creating test movements ---")
created_movements = []

for mv_data in movements_data:
    # Create movement manually to control the date
    delta = mv_data["qty"] if mv_data["type"] == "IN" else -mv_data["qty"]
    new_balance = item.stock_quantity + delta
    item.stock_quantity = new_balance

    movement = models.StockMovement(
        item_id=item.id,
        movement_type=mv_data["type"],
        quantity=mv_data["qty"],
        balance_after=new_balance,
        source_type="Manual",
        source_id=None,
        notes=mv_data["desc"],
        created_by=user.id,
        created_at=mv_data["date"]
    )
    db.add(movement)
    created_movements.append(movement)
    print(f"  {mv_data['date'].strftime('%Y-%m-%d')} | {mv_data['type']:3s} | {mv_data['qty']:3d} | Balance: {new_balance:3d} | {mv_data['desc']}")

db.commit()

print(f"\n[PASS] Created {len(created_movements)} movements")
print(f"  Final stock: {item.stock_quantity}")

# Now test date filtering
print("\n" + "=" * 60)
print("TEST 1: All movements (no filter)")
print("=" * 60)

all_movements = db.query(models.StockMovement).filter(
    models.StockMovement.item_id == item.id
).order_by(models.StockMovement.created_at.asc()).all()

print(f"Expected: 5 movements")
print(f"Actual:   {len(all_movements)} movements")
assert len(all_movements) == 5, f"Expected 5 movements, got {len(all_movements)}"
print("[PASS] PASS")

# Test 2: Filter by date_from only
print("\n" + "=" * 60)
print("TEST 2: Filter by date_from (June 5, 2026)")
print("=" * 60)

date_from = datetime(2026, 6, 5, 0, 0, 0)
filtered_from = db.query(models.StockMovement).filter(
    models.StockMovement.item_id == item.id,
    models.StockMovement.created_at >= date_from
).order_by(models.StockMovement.created_at.asc()).all()

print(f"Date filter: >= {date_from.strftime('%Y-%m-%d')}")
print(f"Expected: 3 movements (June 6, June 8, June 11)")
print(f"Actual:   {len(filtered_from)} movements")

for mv in filtered_from:
    print(f"  {mv.created_at.strftime('%Y-%m-%d')} | {mv.movement_type:3s} | {mv.quantity:3d}")

assert len(filtered_from) == 3, f"Expected 3 movements, got {len(filtered_from)}"
assert filtered_from[0].created_at.date() == datetime(2026, 6, 6).date()
assert filtered_from[1].created_at.date() == datetime(2026, 6, 8).date()
assert filtered_from[2].created_at.date() == datetime(2026, 6, 11).date()
print("[PASS] PASS")

# Test 3: Filter by date_to only
print("\n" + "=" * 60)
print("TEST 3: Filter by date_to (June 7, 2026)")
print("=" * 60)

date_to = datetime(2026, 6, 7, 23, 59, 59)
filtered_to = db.query(models.StockMovement).filter(
    models.StockMovement.item_id == item.id,
    models.StockMovement.created_at <= date_to
).order_by(models.StockMovement.created_at.asc()).all()

print(f"Date filter: <= {date_to.strftime('%Y-%m-%d')}")
print(f"Expected: 3 movements (June 1, June 3, June 6)")
print(f"Actual:   {len(filtered_to)} movements")

for mv in filtered_to:
    print(f"  {mv.created_at.strftime('%Y-%m-%d')} | {mv.movement_type:3s} | {mv.quantity:3d}")

assert len(filtered_to) == 3, f"Expected 3 movements, got {len(filtered_to)}"
assert filtered_to[0].created_at.date() == datetime(2026, 6, 1).date()
assert filtered_to[1].created_at.date() == datetime(2026, 6, 3).date()
assert filtered_to[2].created_at.date() == datetime(2026, 6, 6).date()
print("[PASS] PASS")

# Test 4: Filter by date range (both from and to)
print("\n" + "=" * 60)
print("TEST 4: Filter by date range (June 4 to June 9)")
print("=" * 60)

date_from_range = datetime(2026, 6, 4, 0, 0, 0)
date_to_range = datetime(2026, 6, 9, 23, 59, 59)
filtered_range = db.query(models.StockMovement).filter(
    models.StockMovement.item_id == item.id,
    models.StockMovement.created_at >= date_from_range,
    models.StockMovement.created_at <= date_to_range
).order_by(models.StockMovement.created_at.asc()).all()

print(f"Date filter: {date_from_range.strftime('%Y-%m-%d')} to {date_to_range.strftime('%Y-%m-%d')}")
print(f"Expected: 2 movements (June 6, June 8)")
print(f"Actual:   {len(filtered_range)} movements")

for mv in filtered_range:
    print(f"  {mv.created_at.strftime('%Y-%m-%d')} | {mv.movement_type:3s} | {mv.quantity:3d}")

assert len(filtered_range) == 2, f"Expected 2 movements, got {len(filtered_range)}"
assert filtered_range[0].created_at.date() == datetime(2026, 6, 6).date()
assert filtered_range[1].created_at.date() == datetime(2026, 6, 8).date()
print("[PASS] PASS")

# Test 5: Narrow date range (single day)
print("\n" + "=" * 60)
print("TEST 5: Filter by single day (June 6, 2026)")
print("=" * 60)

date_single_start = datetime(2026, 6, 6, 0, 0, 0)
date_single_end = datetime(2026, 6, 6, 23, 59, 59)
filtered_single = db.query(models.StockMovement).filter(
    models.StockMovement.item_id == item.id,
    models.StockMovement.created_at >= date_single_start,
    models.StockMovement.created_at <= date_single_end
).order_by(models.StockMovement.created_at.asc()).all()

print(f"Date filter: {date_single_start.strftime('%Y-%m-%d')} (single day)")
print(f"Expected: 1 movement (June 6)")
print(f"Actual:   {len(filtered_single)} movements")

for mv in filtered_single:
    print(f"  {mv.created_at.strftime('%Y-%m-%d')} | {mv.movement_type:3s} | {mv.quantity:3d}")

assert len(filtered_single) == 1, f"Expected 1 movement, got {len(filtered_single)}"
assert filtered_single[0].created_at.date() == datetime(2026, 6, 6).date()
print("[PASS] PASS")

# Test 6: No results in date range
print("\n" + "=" * 60)
print("TEST 6: No results (June 20-25, 2026)")
print("=" * 60)

date_empty_start = datetime(2026, 6, 20, 0, 0, 0)
date_empty_end = datetime(2026, 6, 25, 23, 59, 59)
filtered_empty = db.query(models.StockMovement).filter(
    models.StockMovement.item_id == item.id,
    models.StockMovement.created_at >= date_empty_start,
    models.StockMovement.created_at <= date_empty_end
).order_by(models.StockMovement.created_at.asc()).all()

print(f"Date filter: {date_empty_start.strftime('%Y-%m-%d')} to {date_empty_end.strftime('%Y-%m-%d')}")
print(f"Expected: 0 movements")
print(f"Actual:   {len(filtered_empty)} movements")

assert len(filtered_empty) == 0, f"Expected 0 movements, got {len(filtered_empty)}"
print("[PASS] PASS")

# Test 7: Movement type filtering with date range
print("\n" + "=" * 60)
print("TEST 7: Filter by type (IN) + date range (June 1-10)")
print("=" * 60)

date_type_start = datetime(2026, 6, 1, 0, 0, 0)
date_type_end = datetime(2026, 6, 10, 23, 59, 59)
filtered_type = db.query(models.StockMovement).filter(
    models.StockMovement.item_id == item.id,
    models.StockMovement.movement_type == "IN",
    models.StockMovement.created_at >= date_type_start,
    models.StockMovement.created_at <= date_type_end
).order_by(models.StockMovement.created_at.asc()).all()

print(f"Date filter: {date_type_start.strftime('%Y-%m-%d')} to {date_type_end.strftime('%Y-%m-%d')}")
print(f"Type filter: IN")
print(f"Expected: 2 movements (June 1 IN, June 6 IN)")
print(f"Actual:   {len(filtered_type)} movements")

for mv in filtered_type:
    print(f"  {mv.created_at.strftime('%Y-%m-%d')} | {mv.movement_type:3s} | {mv.quantity:3d}")

assert len(filtered_type) == 2, f"Expected 2 IN movements, got {len(filtered_type)}"
assert filtered_type[0].movement_type == "IN"
assert filtered_type[1].movement_type == "IN"
print("[PASS] PASS")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("[PASS] All date range filtering tests passed!")
print(f"  Total movements created: {len(created_movements)}")
print(f"  Tests executed: 7")
print(f"  Tests passed: 7")
print("\nDate filtering works correctly:")
print("  • Filter by date_from only")
print("  • Filter by date_to only")
print("  • Filter by date range (from + to)")
print("  • Filter single day")
print("  • Handle empty results")
print("  • Combine with movement type filtering")
print("\n[PASS] DATE RANGE FILTERING TEST COMPLETE")
