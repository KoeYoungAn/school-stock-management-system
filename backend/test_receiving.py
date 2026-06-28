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


print(f"\n--- Test 4: Receive More PO Status Validations (NEW) ---")

# Setup new POs for testing receive_more specific status validation
po_rm_draft = models.PurchaseOrder(po_number="RM-DRAFT", supplier_id=supplier.id, status="Draft")
po_rm_sent = models.PurchaseOrder(po_number="RM-SENT", supplier_id=supplier.id, status="Sent")
po_rm_cancelled = models.PurchaseOrder(po_number="RM-CANCELLED", supplier_id=supplier.id, status="Cancelled")
po_rm_closed = models.PurchaseOrder(po_number="RM-CLOSED", supplier_id=supplier.id, status="Closed")
po_rm_received = models.PurchaseOrder(po_number="RM-RECEIVED", supplier_id=supplier.id, status="Received")
po_rm_approved = models.PurchaseOrder(po_number="RM-APPROVED", supplier_id=supplier.id, status="Approved")
po_rm_partially_received = models.PurchaseOrder(po_number="RM-PARTIAL", supplier_id=supplier.id, status="Partially Received")

db.add_all([po_rm_draft, po_rm_sent, po_rm_cancelled, po_rm_closed, po_rm_received, po_rm_approved, po_rm_partially_received])
db.commit()

poi_rm_draft = models.PurchaseOrderItem(purchase_order_id=po_rm_draft.id, item_id=item.id, quantity_ordered=5, quantity_received=0)
poi_rm_sent = models.PurchaseOrderItem(purchase_order_id=po_rm_sent.id, item_id=item.id, quantity_ordered=5, quantity_received=0)
poi_rm_cancelled = models.PurchaseOrderItem(purchase_order_id=po_rm_cancelled.id, item_id=item.id, quantity_ordered=5, quantity_received=0)
poi_rm_closed = models.PurchaseOrderItem(purchase_order_id=po_rm_closed.id, item_id=item.id, quantity_ordered=5, quantity_received=0)
poi_rm_received = models.PurchaseOrderItem(purchase_order_id=po_rm_received.id, item_id=item.id, quantity_ordered=5, quantity_received=5)
poi_rm_approved = models.PurchaseOrderItem(purchase_order_id=po_rm_approved.id, item_id=item.id, quantity_ordered=5, quantity_received=0)
poi_rm_partially_received = models.PurchaseOrderItem(purchase_order_id=po_rm_partially_received.id, item_id=item.id, quantity_ordered=5, quantity_received=2)

db.add_all([poi_rm_draft, poi_rm_sent, poi_rm_cancelled, poi_rm_closed, poi_rm_received, poi_rm_approved, poi_rm_partially_received])
db.commit()

# Test cases for invalid statuses
invalid_rm_tests = [
    (po_rm_draft, poi_rm_draft, "Draft"),
    (po_rm_sent, poi_rm_sent, "Sent"),
    (po_rm_cancelled, poi_rm_cancelled, "Cancelled"),
    (po_rm_closed, poi_rm_closed, "Closed"),
    (po_rm_received, poi_rm_received, "Received"),
]

for p, pi, status_name in invalid_rm_tests:
    try:
        payload_rm_invalid = schemas.ReceiveMoreRequest(
            additional_quantity=1,
            receiver_name="Test User",
            status="Received"
        )
        receive_more(pi.id, payload_rm_invalid, db, user)
        assert False, f"Should not allow receive_more from PO status {status_name}"
    except HTTPException as e:
        assert e.status_code == 400
        expected_error_msg = f"Cannot receive stock for a Purchase Order with status '{status_name}'. Only Approved or Partially Received purchase orders can receive stock."
        assert e.detail == expected_error_msg, f"Expected '{expected_error_msg}', got '{e.detail}'"
        print(f"Successfully blocked receive_more from {status_name} PO")

# Test cases for valid statuses
print(f"\n--- Test 5: Receive More PO Status Validations (Valid) ---")

# Approved PO
original_stock_approved = item.stock_quantity
try:
    payload_rm_approved = schemas.ReceiveMoreRequest(
        additional_quantity=3,
        receiver_name="Test User",
        status="Received"
    )
    receive_more(poi_rm_approved.id, payload_rm_approved, db, user)
    db.refresh(poi_rm_approved)
    db.refresh(item)
    db.refresh(po_rm_approved)
    assert poi_rm_approved.quantity_received == 3, "Approved PO: received quantity incorrect"
    assert item.stock_quantity == original_stock_approved + 3, "Approved PO: inventory stock incorrect"
    assert po_rm_approved.status == "Partially Received", "Approved PO: status should be Partially Received"
    print(f"Successfully allowed receive_more from Approved PO. New PO status: {po_rm_approved.status}")
except HTTPException as e:
    assert False, f"Should allow receive_more from Approved PO, but got {e.detail}"

# Partially Received PO
original_stock_partial = item.stock_quantity
try:
    payload_rm_partial = schemas.ReceiveMoreRequest(
        additional_quantity=2,
        receiver_name="Test User",
        status="Received"
    )
    receive_more(poi_rm_partially_received.id, payload_rm_partial, db, user)
    db.refresh(poi_rm_partially_received)
    db.refresh(item)
    db.refresh(po_rm_partially_received)
    assert poi_rm_partially_received.quantity_received == 4, "Partially Received PO: received quantity incorrect"
    assert item.stock_quantity == original_stock_partial + 2, "Partially Received PO: inventory stock incorrect"
    assert po_rm_partially_received.status == "Partially Received", "Partially Received PO: status should remain Partially Received"
    print(f"Successfully allowed receive_more from Partially Received PO. New PO status: {po_rm_partially_received.status}")
except HTTPException as e:
    assert False, f"Should allow receive_more from Partially Received PO, but got {e.detail}"

print(f"\n--- Test 6: Receive More Cannot Exceed Remaining Quantity (NEW) ---")

po_rm_exceed = models.PurchaseOrder(po_number="RM-EXCEED", supplier_id=supplier.id, status="Approved")
db.add(po_rm_exceed)
db.commit()
poi_rm_exceed = models.PurchaseOrderItem(purchase_order_id=po_rm_exceed.id, item_id=item.id, quantity_ordered=5, quantity_received=0)
db.add(poi_rm_exceed)
db.commit()

try:
    payload_rm_exceed = schemas.ReceiveMoreRequest(
        additional_quantity=6, # Exceeds ordered quantity of 5
        receiver_name="Test User",
        status="Received"
    )
    receive_more(poi_rm_exceed.id, payload_rm_exceed, db, user)
    assert False, "Should not allow receive_more to exceed remaining quantity"
except HTTPException as e:
    assert e.status_code == 400
    expected_error_msg_exceed = f"Cannot receive more than remaining quantity (5)"
    assert e.detail == expected_error_msg_exceed, f"Expected '{expected_error_msg_exceed}', got '{e.detail}'"
    print("Successfully blocked receive_more from exceeding remaining quantity")

print(f"\n--- Test 7: Automatic PO Status Update (Fully Received) ---")

# Approved PO becoming fully Received
po_full_rcv = models.PurchaseOrder(po_number="PO-FULL-RCV", supplier_id=supplier.id, status="Approved")
db.add(po_full_rcv)
db.commit()
poi_full_rcv = models.PurchaseOrderItem(purchase_order_id=po_full_rcv.id, item_id=item.id, quantity_ordered=5, quantity_received=0)
db.add(poi_full_rcv)
db.commit()

try:
    payload_full_rcv = schemas.ReceiveMoreRequest(
        additional_quantity=5,
        receiver_name="Test User",
        status="Received"
    )
    receive_more(poi_full_rcv.id, payload_full_rcv, db, user)
    db.refresh(po_full_rcv)
    assert po_full_rcv.status == "Received", "PO status should become 'Received' after full receipt"
    print("Successfully updated PO status to 'Received' automatically.")
except HTTPException as e:
    assert False, f"Failed to fully receive PO: {e.detail}"

print(f"\n--- Test 8: _refresh_po_status does not override Cancelled/Closed (Verification) ---")

po_verify_cancelled = models.PurchaseOrder(po_number="VERIFY-CXL", supplier_id=supplier.id, status="Cancelled")
db.add(po_verify_cancelled)
db.commit()
poi_verify_cancelled = models.PurchaseOrderItem(purchase_order_id=po_verify_cancelled.id, item_id=item.id, quantity_ordered=10, quantity_received=0)
db.add(poi_verify_cancelled)
db.commit()

# Simulate a receiving event that would normally change status (but shouldn't here)
_refresh_po_status(db, po_verify_cancelled.id) # This call should do nothing for Cancelled
db.refresh(po_verify_cancelled)
assert po_verify_cancelled.status == "Cancelled", "_refresh_po_status should not override Cancelled status"
print("Verified: _refresh_po_status does not override Cancelled status.")

po_verify_closed = models.PurchaseOrder(po_number="VERIFY-CLO", supplier_id=supplier.id, status="Closed")
db.add(po_verify_closed)
db.commit()
poi_verify_closed = models.PurchaseOrderItem(purchase_order_id=po_verify_closed.id, item_id=item.id, quantity_ordered=10, quantity_received=5) # Partially received
db.add(poi_verify_closed)
db.commit()

# Simulate a receiving event that would normally change status (but shouldn't here)
_refresh_po_status(db, po_verify_closed.id) # This call should do nothing for Closed
db.refresh(po_verify_closed)
assert po_verify_closed.status == "Closed", "_refresh_po_status should not override Closed status"
print("Verified: _refresh_po_status does not override Closed status.")

print("ALL TESTS PASSED: PO status validations and receiving constraints are fully verified.")
