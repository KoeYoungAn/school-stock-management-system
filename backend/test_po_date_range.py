import os
import sys
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
from crud import list_pos

# In-memory DB
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=" * 60)
print("PURCHASE ORDER DATE RANGE FILTERING TEST")
print("=" * 60)

# Setup test user
user = models.User(email="tester@example.com", role="Admin", full_name="Test Admin", password_hash="hash")
db.add(user)
db.commit()

# Setup test supplier
supplier = models.Supplier(supplier_name="Test Supplier")
db.add(supplier)
db.commit()

print(f"\n[PASS] Created test user and supplier")

# Create POs with different order_date values
base_date = datetime(2026, 6, 1, 10, 0, 0)  # June 1, 2026

pos_data = [
    {"po_number": "PO-001", "order_date": base_date, "expected_date": base_date + timedelta(days=7), "desc": "June 1 order"},
    {"po_number": "PO-002", "order_date": base_date + timedelta(days=2), "expected_date": base_date + timedelta(days=9), "desc": "June 3 order"},
    {"po_number": "PO-003", "order_date": base_date + timedelta(days=5), "expected_date": base_date + timedelta(days=12), "desc": "June 6 order"},
    {"po_number": "PO-004", "order_date": base_date + timedelta(days=7), "expected_date": base_date + timedelta(days=14), "desc": "June 8 order"},
    {"po_number": "PO-005", "order_date": base_date + timedelta(days=10), "expected_date": base_date + timedelta(days=17), "desc": "June 11 order"},
]

print(f"\n--- Creating test POs ---")
created_pos = []

for po_data in pos_data:
    po = models.PurchaseOrder(
        po_number=po_data["po_number"],
        supplier_id=supplier.id,
        order_date=po_data["order_date"],
        expected_delivery_date=po_data["expected_date"],
        status="Draft"
    )
    db.add(po)
    created_pos.append(po)
    print(f"  {po_data['order_date'].strftime('%Y-%m-%d')} | {po_data['po_number']} | Order Date | {po_data['desc']}")
    print(f"  {po_data['expected_date'].strftime('%Y-%m-%d')} | {po_data['po_number']} | Expected Date")

db.commit()

print(f"\n[PASS] Created {len(created_pos)} POs")

# Now test date filtering
print("\n" + "=" * 60)
print("TEST 1: All POs (no filter)")
print("=" * 60)

result = list_pos(page=1, limit=500, search="", status=None, date_from=None, date_to=None, date_filter_by="order_date", db=db, _=user)
all_pos = result["items"]

print(f"Expected: 5 POs")
print(f"Actual:   {len(all_pos)} POs")
assert len(all_pos) == 5, f"Expected 5 POs, got {len(all_pos)}"
print("[PASS] PASS")

# Test 2: Filter by order_date from only
print("\n" + "=" * 60)
print("TEST 2: Filter by order_date >= June 5, 2026")
print("=" * 60)

date_from = "2026-06-05"
result = list_pos(page=1, limit=500, search="", status=None, date_from=date_from, date_to=None, date_filter_by="order_date", db=db, _=user)
filtered_from = result["items"]

print(f"Date filter: order_date >= {date_from}")
print(f"Expected: 3 POs (June 6, June 8, June 11)")
print(f"Actual:   {len(filtered_from)} POs")

for po in filtered_from:
    order_date = datetime.fromisoformat(po["order_date"]) if isinstance(po["order_date"], str) else po["order_date"]
    print(f"  {order_date.strftime('%Y-%m-%d')} | {po['po_number']}")

assert len(filtered_from) == 3, f"Expected 3 POs, got {len(filtered_from)}"
print("[PASS] PASS")

# Test 3: Filter by order_date to only
print("\n" + "=" * 60)
print("TEST 3: Filter by order_date <= June 7, 2026")
print("=" * 60)

date_to = "2026-06-07"
result = list_pos(page=1, limit=500, search="", status=None, date_from=None, date_to=date_to, date_filter_by="order_date", db=db, _=user)
filtered_to = result["items"]

print(f"Date filter: order_date <= {date_to}")
print(f"Expected: 3 POs (June 1, June 3, June 6)")
print(f"Actual:   {len(filtered_to)} POs")

for po in filtered_to:
    order_date = datetime.fromisoformat(po["order_date"]) if isinstance(po["order_date"], str) else po["order_date"]
    print(f"  {order_date.strftime('%Y-%m-%d')} | {po['po_number']}")

assert len(filtered_to) == 3, f"Expected 3 POs, got {len(filtered_to)}"
print("[PASS] PASS")

# Test 4: Filter by order_date range (both from and to)
print("\n" + "=" * 60)
print("TEST 4: Filter by order_date range (June 4 to June 9)")
print("=" * 60)

date_from_range = "2026-06-04"
date_to_range = "2026-06-09"
result = list_pos(page=1, limit=500, search="", status=None, date_from=date_from_range, date_to=date_to_range, date_filter_by="order_date", db=db, _=user)
filtered_range = result["items"]

print(f"Date filter: {date_from_range} to {date_to_range}")
print(f"Expected: 2 POs (June 6, June 8)")
print(f"Actual:   {len(filtered_range)} POs")

for po in filtered_range:
    order_date = datetime.fromisoformat(po["order_date"]) if isinstance(po["order_date"], str) else po["order_date"]
    print(f"  {order_date.strftime('%Y-%m-%d')} | {po['po_number']}")

assert len(filtered_range) == 2, f"Expected 2 POs, got {len(filtered_range)}"
print("[PASS] PASS")

# Test 5: Single day range (June 6, 2026) - INCLUSIVE TEST
print("\n" + "=" * 60)
print("TEST 5: Filter by single day (June 6, 2026)")
print("=" * 60)

date_single = "2026-06-06"
result = list_pos(page=1, limit=500, search="", status=None, date_from=date_single, date_to=date_single, date_filter_by="order_date", db=db, _=user)
filtered_single = result["items"]

print(f"Date filter: {date_single} to {date_single} (same day)")
print(f"Expected: 1 PO (June 6)")
print(f"Actual:   {len(filtered_single)} POs")

for po in filtered_single:
    order_date = datetime.fromisoformat(po["order_date"]) if isinstance(po["order_date"], str) else po["order_date"]
    print(f"  {order_date.strftime('%Y-%m-%d')} | {po['po_number']}")

assert len(filtered_single) == 1, f"Expected 1 PO, got {len(filtered_single)}"
print("[PASS] PASS - Single day inclusive filtering works!")

# Test 6: Two consecutive days (June 6-7, 2026)
print("\n" + "=" * 60)
print("TEST 6: Filter by two consecutive days (June 6-7, 2026)")
print("=" * 60)

date_from_two = "2026-06-06"
date_to_two = "2026-06-07"
result = list_pos(page=1, limit=500, search="", status=None, date_from=date_from_two, date_to=date_to_two, date_filter_by="order_date", db=db, _=user)
filtered_two = result["items"]

print(f"Date filter: {date_from_two} to {date_to_two}")
print(f"Expected: 1 PO (only June 6, since no PO on June 7)")
print(f"Actual:   {len(filtered_two)} POs")

for po in filtered_two:
    order_date = datetime.fromisoformat(po["order_date"]) if isinstance(po["order_date"], str) else po["order_date"]
    print(f"  {order_date.strftime('%Y-%m-%d')} | {po['po_number']}")

assert len(filtered_two) == 1, f"Expected 1 PO, got {len(filtered_two)}"
print("[PASS] PASS")

# Test 7: No results in date range
print("\n" + "=" * 60)
print("TEST 7: No results (June 20-25, 2026)")
print("=" * 60)

date_empty_start = "2026-06-20"
date_empty_end = "2026-06-25"
result = list_pos(page=1, limit=500, search="", status=None, date_from=date_empty_start, date_to=date_empty_end, date_filter_by="order_date", db=db, _=user)
filtered_empty = result["items"]

print(f"Date filter: {date_empty_start} to {date_empty_end}")
print(f"Expected: 0 POs")
print(f"Actual:   {len(filtered_empty)} POs")

assert len(filtered_empty) == 0, f"Expected 0 POs, got {len(filtered_empty)}"
print("[PASS] PASS")

# Test 8: Filter by expected_delivery_date
print("\n" + "=" * 60)
print("TEST 8: Filter by expected_delivery_date (June 10-15, 2026)")
print("=" * 60)

date_from_exp = "2026-06-10"
date_to_exp = "2026-06-15"
result = list_pos(page=1, limit=500, search="", status=None, date_from=date_from_exp, date_to=date_to_exp, date_filter_by="expected_delivery_date", db=db, _=user)
filtered_exp = result["items"]

print(f"Date filter: expected_delivery_date from {date_from_exp} to {date_to_exp}")
print(f"Expected: 3 POs (with expected dates June 10, June 13, June 15)")
print(f"Actual:   {len(filtered_exp)} POs")

for po in filtered_exp:
    expected_date = datetime.fromisoformat(po["expected_delivery_date"]) if isinstance(po["expected_delivery_date"], str) else po["expected_delivery_date"]
    print(f"  {expected_date.strftime('%Y-%m-%d')} | {po['po_number']} | Expected Date")

assert len(filtered_exp) == 3, f"Expected 3 POs, got {len(filtered_exp)}"
print("[PASS] PASS - Expected delivery date filtering works!")

# Test 9: Invalid date range (start > end)
print("\n" + "=" * 60)
print("TEST 9: Invalid date range (start > end)")
print("=" * 60)

date_from_invalid = "2026-06-10"
date_to_invalid = "2026-06-05"

print(f"Date filter: {date_from_invalid} to {date_to_invalid} (invalid: start > end)")
print(f"Expected: HTTPException with 'Start date cannot be after end date.'")

try:
    result = list_pos(page=1, limit=500, search="", status=None, date_from=date_from_invalid, date_to=date_to_invalid, date_filter_by="order_date", db=db, _=user)
    assert False, "Should have raised HTTPException for invalid date range"
except HTTPException as e:
    assert e.status_code == 400
    assert "Start date cannot be after end date" in str(e.detail)
    print(f"Actual: HTTPException(400) - {e.detail}")
    print("[PASS] PASS - Invalid date range rejected!")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("[PASS] All Purchase Order date range filtering tests passed!")
print(f"  Total POs created: {len(created_pos)}")
print(f"  Tests executed: 9")
print(f"  Tests passed: 9")
print("\nPO date filtering works correctly:")
print("  [PASS] Filter by order_date (default)")
print("  [PASS] Filter by expected_delivery_date")
print("  [PASS] Single day inclusive (26-26 returns day 26)")
print("  [PASS] Two day inclusive (26-27 returns days 26 and 27)")
print("  [PASS] Date range validation (start > end rejected)")
print("  [PASS] Empty results handled correctly")
print("\n[PASS] PO DATE RANGE FILTERING TEST COMPLETE")
