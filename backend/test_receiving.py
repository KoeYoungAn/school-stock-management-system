import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
import schemas
from utils import record_movement
from crud import create_rcv, update_rcv, _refresh_po_status, receive_more, create_po, update_po

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


print(f"--- Test 3: Purchase Order Status Rules ---")

# 3.1 Cannot create a new PO as Cancelled or Closed
try:
    payload_po_create = schemas.POCreate(
        supplier_id=supplier.id,
        status="Cancelled",
        items=[schemas.POItemCreate(item_id=item.id, quantity_ordered=5)]
    )
    create_po(payload_po_create, db, user)
    assert False, "Should not allow creating a Cancelled PO"
except HTTPException as e:
    assert e.status_code == 400
    print("Successfully blocked creating a Cancelled PO")

try:
    payload_po_create = schemas.POCreate(
        supplier_id=supplier.id,
        status="Closed",
        items=[schemas.POItemCreate(item_id=item.id, quantity_ordered=5)]
    )
    create_po(payload_po_create, db, user)
    assert False, "Should not allow creating a Closed PO"
except HTTPException as e:
    assert e.status_code == 400
    print("Successfully blocked creating a Closed PO")


# 3.2 Cannot cancel a PO after any item has been received
po_test = models.PurchaseOrder(
    po_number="PO-TEST-1",
    supplier_id=supplier.id,
    status="Partially Received"
)
db.add(po_test)
db.commit()
poi_test = models.PurchaseOrderItem(
    purchase_order_id=po_test.id,
    item_id=item.id,
    quantity_ordered=10,
    quantity_received=3
)
db.add(poi_test)
db.commit()

try:
    update_po(po_test.id, schemas.POUpdate(status="Cancelled"), db, user)
    assert False, "Should not allow cancelling a PO with received items"
except HTTPException as e:
    assert e.status_code == 400
    print("Successfully blocked cancelling a PO with received items")


# 3.3 Can close a partially received PO
update_po(po_test.id, schemas.POUpdate(status="Closed"), db, user)
db.refresh(po_test)
assert po_test.status == "Closed", "PO should be Closed"
print("Successfully closed a partially received PO")


# 3.4 Cannot receive stock from Draft, Sent, Cancelled, Closed, or Received PO
po_draft = models.PurchaseOrder(po_number="PO-DRAFT", supplier_id=supplier.id, status="Draft")
po_sent = models.PurchaseOrder(po_number="PO-SENT", supplier_id=supplier.id, status="Sent")
po_cancelled = models.PurchaseOrder(po_number="PO-CANCELLED", supplier_id=supplier.id, status="Cancelled")
po_closed = models.PurchaseOrder(po_number="PO-CLOSED", supplier_id=supplier.id, status="Closed")
po_received = models.PurchaseOrder(po_number="PO-RECEIVED", supplier_id=supplier.id, status="Received")
db.add_all([po_draft, po_sent, po_cancelled, po_closed, po_received])
db.commit()

poi_draft = models.PurchaseOrderItem(purchase_order_id=po_draft.id, item_id=item.id, quantity_ordered=5)
poi_sent = models.PurchaseOrderItem(purchase_order_id=po_sent.id, item_id=item.id, quantity_ordered=5)
poi_cancelled = models.PurchaseOrderItem(purchase_order_id=po_cancelled.id, item_id=item.id, quantity_ordered=5)
poi_closed = models.PurchaseOrderItem(purchase_order_id=po_closed.id, item_id=item.id, quantity_ordered=5)
poi_received = models.PurchaseOrderItem(purchase_order_id=po_received.id, item_id=item.id, quantity_ordered=5, quantity_received=5)
db.add_all([poi_draft, poi_sent, poi_cancelled, poi_closed, poi_received])
db.commit()

invalid_pos = [po_draft, po_sent, po_cancelled, po_closed, po_received]
invalid_pois = [poi_draft, poi_sent, poi_cancelled, poi_closed, poi_received]

for p, pi in zip(invalid_pos, invalid_pois):
    try:
        payload_rcv = schemas.ReceivingCreate(
            purchase_order_id=p.id,
            purchase_order_item_id=pi.id,
            item_id=item.id,
            quantity_received=1,
            receiver_name="Admin",
            status="Received"
        )
        create_rcv(payload_rcv, db, user)
        assert False, f"Should not allow receiving from PO status {p.status}"
    except HTTPException as e:
        assert e.status_code == 400
        print(f"Successfully blocked receiving from {p.status} PO")

print("ALL TESTS PASSED: PO status validations and receiving constraints are fully verified.")