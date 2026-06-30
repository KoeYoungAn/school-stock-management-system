"""
Phase 5B Testing: Receive from PO Unit Conversion Support

Tests verify:
1. ITM-009 can be received from PO using box units (1 box = 10 pieces)
2. Inventory stock increases in base units (pieces)
3. Over-receiving is rejected with proper validation
4. PO status updates correctly (Partially Received, Received)
5. Direct Stock Receipt from Phase 5A still works
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
import crud
import schemas
from datetime import datetime

# Test database setup
TEST_DB = "sqlite:///./test_phase5b.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def db():
    """Create test database and session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db):
    """Create test user"""
    user = models.User(
        username="testuser",
        email="test@test.com",
        password_hash="test",
        role="staff"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def setup_itm009(db):
    """Setup ITM-009 with box units and conversions"""
    # Create base unit: piece
    piece_unit = models.Unit(name="piece", abbreviation="pcs")
    box_unit = models.Unit(name="box", abbreviation="box")
    db.add_all([piece_unit, box_unit])
    db.commit()

    # Create ITM-009 notebook item
    item = models.InventoryItem(
        item_code="ITM-009",
        item_name="notebook",
        category="Stationery",
        base_unit_id=piece_unit.id,
        stock_quantity=110,  # Current stock: 110 pieces
        minimum_stock=50,
        unit="pcs"
    )
    db.add(item)
    db.commit()

    # Create conversion: 1 box = 10 pieces
    conversion = models.ItemUnitConversion(
        item_id=item.id,
        purchase_unit_id=box_unit.id,
        conversion_factor=10,
        is_default_purchase_unit=True
    )
    db.add(conversion)
    db.commit()

    return {
        "item": item,
        "piece_unit": piece_unit,
        "box_unit": box_unit,
        "conversion": conversion
    }

@pytest.fixture
def setup_po_for_itm009(db, setup_itm009, test_user):
    """Setup Purchase Order for ITM-009"""
    # Create supplier
    supplier = models.Supplier(
        name="Test Supplier",
        contact_person="John Doe",
        email="supplier@test.com",
        phone="1234567890"
    )
    db.add(supplier)
    db.commit()

    # Create PO
    po = models.PurchaseOrder(
        po_number="PO-TEST-001",
        supplier_id=supplier.id,
        status="Approved",
        order_date=datetime.now(),
        created_by=test_user.id
    )
    db.add(po)
    db.commit()

    # Create PO item: Order 50 pieces (5 boxes equivalent)
    po_item = models.PurchaseOrderItem(
        purchase_order_id=po.id,
        item_id=setup_itm009["item"].id,
        quantity_ordered=50,  # In base units (pieces)
        quantity_received=0,
        unit_price=10.0
    )
    db.add(po_item)
    db.commit()

    return {
        "po": po,
        "po_item": po_item,
        "supplier": supplier
    }


# ============================================================
# TEST 1: ITM-009 PO Receiving with Box Units
# ============================================================

def test_itm009_receive_from_po_using_boxes(db, setup_itm009, setup_po_for_itm009, test_user):
    """
    Test: Receive 2 boxes from PO for ITM-009
    Expected:
    - 2 boxes = 20 pieces (conversion)
    - Stock increases from 110 to 130 pieces
    - PO item received quantity updates to 20 pieces
    - Receiving record stores conversion context
    """
    item = setup_itm009["item"]
    box_unit = setup_itm009["box_unit"]
    po_item = setup_po_for_itm009["po_item"]

    # Initial state verification
    assert item.stock_quantity == 110, "Initial stock should be 110 pieces"
    assert po_item.quantity_ordered == 50, "PO ordered quantity should be 50 pieces"
    assert po_item.quantity_received == 0, "PO received quantity should be 0"

    # Receive 2 boxes from PO
    payload = schemas.ReceiveMoreRequest(
        received_unit_id=box_unit.id,
        quantity_received=2,  # 2 boxes
        receiver_name="Test Receiver",
        status="Received",
        notes="Phase 5B test"
    )

    result = crud.receive_more(po_item.id, payload, db, test_user)

    # Verify response
    assert result["quantity_display"] == 2, "Should display 2 boxes"
    assert result["unit_name"] == "box", "Unit name should be box"
    assert result["base_quantity"] == 20, "Base quantity should be 20 pieces"
    assert result["conversion_display"] == "2 box = 20 piece", "Conversion display should show 2 box = 20 piece"
    assert result["new_total_received"] == 20, "Total received should be 20 pieces"
    assert result["remaining"] == 30, "Remaining should be 30 pieces (50 - 20)"

    # Refresh from database
    db.refresh(item)
    db.refresh(po_item)

    # Verify stock increased by 20 pieces
    assert item.stock_quantity == 130, "Stock should increase from 110 to 130 pieces"

    # Verify PO item received quantity
    assert po_item.quantity_received == 20, "PO item received should be 20 pieces"

    # Verify receiving record
    receiving = db.query(models.Receiving).filter(
        models.Receiving.purchase_order_item_id == po_item.id
    ).first()
    assert receiving is not None, "Receiving record should exist"
    assert receiving.quantity_received == 20, "Receiving record should store base quantity (20 pieces)"
    assert receiving.received_unit_id == box_unit.id, "Receiving should store received unit"
    assert receiving.conversion_factor == 10, "Conversion factor should be 10"
    assert receiving.received_quantity_display == 2, "Display quantity should be 2 boxes"

    print("✅ TEST 1 PASSED: ITM-009 receives 2 boxes = 20 pieces, stock increases correctly")


# ============================================================
# TEST 2: Over-receiving Rejection
# ============================================================

def test_over_receiving_rejected(db, setup_itm009, setup_po_for_itm009, test_user):
    """
    Test: Attempt to receive more than remaining quantity
    Expected:
    - Request rejected with error
    - Stock unchanged
    - PO item unchanged
    """
    item = setup_itm009["item"]
    box_unit = setup_itm009["box_unit"]
    po_item = setup_po_for_itm009["po_item"]

    initial_stock = item.stock_quantity

    # Attempt to receive 10 boxes (100 pieces) when only 50 pieces ordered
    payload = schemas.ReceiveMoreRequest(
        received_unit_id=box_unit.id,
        quantity_received=10,  # 10 boxes = 100 pieces > 50 pieces ordered
        receiver_name="Test Receiver",
        status="Received",
        notes="Over-receive test"
    )

    # Should raise HTTPException
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        crud.receive_more(po_item.id, payload, db, test_user)

    assert exc_info.value.status_code == 400, "Should return 400 error"
    assert "Cannot receive more than remaining quantity" in str(exc_info.value.detail), "Error message should mention remaining quantity"

    # Verify stock unchanged
    db.refresh(item)
    db.refresh(po_item)
    assert item.stock_quantity == initial_stock, "Stock should remain unchanged"
    assert po_item.quantity_received == 0, "PO received should remain 0"

    print("✅ TEST 2 PASSED: Over-receiving correctly rejected")


# ============================================================
# TEST 3: PO Status Updates - Partially Received
# ============================================================

def test_po_status_partially_received(db, setup_itm009, setup_po_for_itm009, test_user):
    """
    Test: Partial receipt updates PO status to 'Partially Received'
    Expected:
    - After receiving part of order, PO status = 'Partially Received'
    """
    box_unit = setup_itm009["box_unit"]
    po = setup_po_for_itm009["po"]
    po_item = setup_po_for_itm009["po_item"]

    assert po.status == "Approved", "Initial PO status should be Approved"

    # Receive 2 boxes (20 pieces) out of 50 pieces ordered
    payload = schemas.ReceiveMoreRequest(
        received_unit_id=box_unit.id,
        quantity_received=2,  # 2 boxes = 20 pieces
        receiver_name="Test Receiver",
        status="Received"
    )

    crud.receive_more(po_item.id, payload, db, test_user)

    # Refresh PO
    db.refresh(po)

    # Verify PO status updated to Partially Received
    assert po.status == "Partially Received", "PO status should be 'Partially Received' after partial receipt"

    print("✅ TEST 3 PASSED: PO status updates to 'Partially Received'")


# ============================================================
# TEST 4: PO Status Updates - Fully Received
# ============================================================

def test_po_status_fully_received(db, setup_itm009, setup_po_for_itm009, test_user):
    """
    Test: Full receipt updates PO status to 'Received'
    Expected:
    - After receiving all ordered items, PO status = 'Received'
    """
    box_unit = setup_itm009["box_unit"]
    po = setup_po_for_itm009["po"]
    po_item = setup_po_for_itm009["po_item"]

    # Receive all 50 pieces (5 boxes)
    payload = schemas.ReceiveMoreRequest(
        received_unit_id=box_unit.id,
        quantity_received=5,  # 5 boxes = 50 pieces (full order)
        receiver_name="Test Receiver",
        status="Received"
    )

    crud.receive_more(po_item.id, payload, db, test_user)

    # Refresh PO and PO item
    db.refresh(po)
    db.refresh(po_item)

    # Verify full receipt
    assert po_item.quantity_received == 50, "All 50 pieces should be received"
    assert po_item.quantity_ordered == po_item.quantity_received, "Received should equal ordered"

    # Verify PO status updated to Received
    assert po.status == "Received", "PO status should be 'Received' after full receipt"

    print("✅ TEST 4 PASSED: PO status updates to 'Received' after full receipt")


# ============================================================
# TEST 5: Direct Stock Receipt Still Works (Phase 5A)
# ============================================================

def test_direct_stock_receipt_still_works(db, setup_itm009, test_user):
    """
    Test: Direct Stock Receipt from Phase 5A still works
    Expected:
    - Can receive stock directly without PO
    - Stock increases correctly
    - Unit conversion works
    """
    item = setup_itm009["item"]
    box_unit = setup_itm009["box_unit"]

    initial_stock = item.stock_quantity  # 110 pieces

    # Direct receipt: 3 boxes
    payload = schemas.DirectReceiptCreate(
        item_id=item.id,
        received_unit_id=box_unit.id,
        quantity_received=3,  # 3 boxes = 30 pieces
        source="Donation",
        reason="Test direct receipt",
        receiver_name="Test Receiver",
        notes="Phase 5A compatibility test"
    )

    result = crud.create_direct_receipt(payload, db, test_user)

    # Verify response
    assert result["conversion_display"] == "3 box = 30 piece", "Conversion display should be correct"
    assert result["new_stock"] == initial_stock + 30, "New stock should be 140 pieces"

    # Refresh from database
    db.refresh(item)

    # Verify stock increased
    assert item.stock_quantity == initial_stock + 30, "Stock should increase by 30 pieces (3 boxes)"

    # Verify receiving record created
    receiving = db.query(models.Receiving).filter(
        models.Receiving.item_id == item.id,
        models.Receiving.purchase_order_id == None
    ).first()
    assert receiving is not None, "Direct receipt record should exist"
    assert receiving.quantity_received == 30, "Should store base quantity"
    assert receiving.received_unit_id == box_unit.id, "Should store received unit"
    assert receiving.conversion_factor == 10, "Should store conversion factor"
    assert receiving.received_quantity_display == 3, "Should store display quantity"

    print("✅ TEST 5 PASSED: Direct Stock Receipt (Phase 5A) still works correctly")


# ============================================================
# Run all tests
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 5B Comprehensive Testing")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
