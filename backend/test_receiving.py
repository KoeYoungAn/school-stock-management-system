import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, r"D:\IT year 4 final project\school-stock-management-system - Copy (4)\backend")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
import schemas
from utils import record_movement
from crud import create_rcv, update_rcv, _refresh_po_status, receive_more

# In-memory DB
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Setup dummy data with correct fields
user = models.User(email="admin@example.com", role="Admin", full_name="Admin", password_hash="hash")
db.add(user)
db.commit()

# Setup item ITM-007
item = models.InventoryItem(
    item_code="ITM-007",
    item_name="Monitor",
    stock_quantity=5, # Starting with 5
    category="Electronics"
)
db.add(item)
db.commit()

# Setup supplier, PO and PO Item
supplier = models.Supplier(supplier_name="Test Supplier")
db.add(supplier)
db.commit()

po = models.PurchaseOrder(
    po_number="PO-001",
    supplier_id=supplier.id,
    status="Partially Received"
)
db.add(po)
db.commit()

poi = models.PurchaseOrderItem(
    purchase_order_id=po.id,
    item_id=item.id,
    quantity_ordered=10,
    quantity_received=5 # Already received 5
)
db.add(poi)
db.commit()

# Ensure we have a first receiving record
r1 = models.Receiving(
    receiving_number="RCV-001",
    purchase_order_id=po.id,
    purchase_order_item_id=poi.id,
    item_id=item.id,
    quantity_received=5,
    status="Received",
    receiver_name="Admin"
)
db.add(r1)
db.commit()

print(f"--- Initial State ---")
print(f"Ordered: {poi.quantity_ordered}")
print(f"Received: {poi.quantity_received}")
print(f"Remaining: {poi.quantity_ordered - poi.quantity_received}")
print(f"Inventory: {item.stock_quantity}")
print()

print(f"--- Test 1: Receive 2 More (Using NEW ReceiveMore Endpoint) ---")
payload_rm = schemas.ReceiveMoreRequest(
    additional_quantity=2,
    receiver_name="Admin",
    status="Received",
    notes="Receive more test"
)
receive_more(poi.id, payload_rm, db, user)

db.refresh(poi)
db.refresh(item)

print(f"Ordered: {poi.quantity_ordered}")
print(f"Received: {poi.quantity_received}")
print(f"Remaining: {poi.quantity_ordered - poi.quantity_received}")
print(f"Inventory: {item.stock_quantity}")
print()

assert poi.quantity_received == 7, "Received quantity should be 7"
assert item.stock_quantity == 7, "Inventory should be 7"

print(f"--- Test 2: Edit Receiving Record (Correct quantity) ---")
# Simulate editing the first record (e.g. from 5 to 6)
payload_update = schemas.ReceivingUpdate(
    quantity_received=6,
    status="Received"
)
update_rcv(r1.id, payload_update, db, user)

db.refresh(poi)
db.refresh(item)

print(f"Ordered: {poi.quantity_ordered}")
print(f"Received: {poi.quantity_received}")
print(f"Remaining: {poi.quantity_ordered - poi.quantity_received}")
print(f"Inventory: {item.stock_quantity}")
print()

assert poi.quantity_received == 8, "Received quantity should be 8 (6 + 2)"
assert item.stock_quantity == 8, "Inventory should be 8 (6 + 2)"

print("ALL TESTS PASSED: Receive More properly accumulates and corrections apply delta.")