"""
Backend tests for Phase 2: Units System Foundation

Tests cover:
- Units CRUD operations
- ItemUnitConversion CRUD operations
- get_conversion_factor helper
- Database schema integrity
- Data preservation (existing stock quantities)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models
from utils import get_conversion_factor

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase2.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    """Test client with fresh database"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def admin_token(client, db):
    """Create admin user and return auth token"""
    from utils import hash_password
    admin = models.User(
        full_name="Test Admin",
        email="admin@test.local",
        role="Admin",
        status="Active",
        password_hash=hash_password("test123")
    )
    db.add(admin)
    db.commit()

    response = client.post("/api/auth/login", json={"email": "admin@test.local", "password": "test123"})
    return response.json()["access_token"]

@pytest.fixture
def staff_token(client, db):
    """Create storekeeper user and return auth token"""
    from utils import hash_password
    staff = models.User(
        full_name="Test Staff",
        email="staff@test.local",
        role="Storekeeper",
        status="Active",
        password_hash=hash_password("test123")
    )
    db.add(staff)
    db.commit()

    response = client.post("/api/auth/login", json={"email": "staff@test.local", "password": "test123"})
    return response.json()["access_token"]


# ============================================================
# DATABASE SCHEMA TESTS
# ============================================================

def test_units_table_exists(db):
    """Test that units table was created"""
    inspector = inspect(engine)
    assert 'units' in inspector.get_table_names()

def test_item_unit_conversions_table_exists(db):
    """Test that item_unit_conversions table was created"""
    inspector = inspect(engine)
    assert 'item_unit_conversions' in inspector.get_table_names()

def test_inventory_items_has_base_unit_id(db):
    """Test that inventory_items table has base_unit_id column"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('inventory_items')]
    assert 'base_unit_id' in columns

def test_inventory_items_still_has_old_unit_field(db):
    """Test that old 'unit' text field is preserved"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('inventory_items')]
    assert 'unit' in columns


# ============================================================
# UNIT CRUD TESTS
# ============================================================

def test_can_create_unit(client, admin_token, db):
    """Test creating a new unit"""
    response = client.post(
        "/api/units",
        json={"name": "kilogram", "abbreviation": "kg", "description": "Unit of mass", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "id" in response.json()

    # Verify in database
    unit = db.query(models.Unit).filter(models.Unit.name == "kilogram").first()
    assert unit is not None
    assert unit.abbreviation == "kg"

def test_cannot_create_duplicate_unit(client, admin_token, db):
    """Test that duplicate unit names are rejected"""
    # Create first unit
    client.post(
        "/api/units",
        json={"name": "piece", "abbreviation": "pcs"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Try to create duplicate
    response = client.post(
        "/api/units",
        json={"name": "piece", "abbreviation": "pc"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400

def test_can_list_units(client, admin_token, db):
    """Test listing units"""
    # Create some units
    units_to_create = [
        models.Unit(name="piece", abbreviation="pcs", is_active=True),
        models.Unit(name="box", abbreviation="box", is_active=True),
        models.Unit(name="dozen", abbreviation="doz", is_active=True)
    ]
    for u in units_to_create:
        db.add(u)
    db.commit()

    response = client.get("/api/units", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3

def test_can_update_unit(client, admin_token, db):
    """Test updating a unit"""
    # Create unit
    unit = models.Unit(name="piece", abbreviation="pcs")
    db.add(unit)
    db.commit()

    # Update it
    response = client.put(
        f"/api/units/{unit.id}",
        json={"description": "Updated description"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

    db.refresh(unit)
    assert unit.description == "Updated description"

def test_can_deactivate_unit(client, admin_token, db):
    """Test deactivating a unit"""
    # Create unit
    unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    db.add(unit)
    db.commit()

    # Deactivate it
    response = client.delete(
        f"/api/units/{unit.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

    db.refresh(unit)
    assert unit.is_active == False

def test_cannot_deactivate_unit_in_use(client, admin_token, db):
    """Test that units in use cannot be deactivated"""
    # Create unit and item using it
    unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    db.add(unit)
    db.commit()

    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        base_unit_id=unit.id,
        unit="pcs",
        stock_quantity=10
    )
    db.add(item)
    db.commit()

    # Try to deactivate
    response = client.delete(
        f"/api/units/{unit.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409


# ============================================================
# ITEM UNIT CONVERSION TESTS
# ============================================================

def test_can_create_conversion(client, staff_token, db):
    """Test creating an item unit conversion"""
    # Create units and item
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    purchase_unit = models.Unit(name="box", abbreviation="box", is_active=True)
    db.add_all([base_unit, purchase_unit])
    db.commit()

    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        base_unit_id=base_unit.id,
        unit="pcs",
        stock_quantity=100
    )
    db.add(item)
    db.commit()

    # Create conversion
    response = client.post(
        "/api/item-conversions",
        json={
            "item_id": item.id,
            "purchase_unit_id": purchase_unit.id,
            "conversion_factor": 12,
            "is_default_purchase_unit": True
        },
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert response.status_code == 200

    # Verify in database
    conversion = db.query(models.ItemUnitConversion).filter(
        models.ItemUnitConversion.item_id == item.id
    ).first()
    assert conversion is not None
    assert conversion.conversion_factor == 12

def test_conversion_factor_must_be_positive(client, staff_token, db):
    """Test that conversion_factor must be > 0"""
    # Create units and item
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    purchase_unit = models.Unit(name="box", abbreviation="box", is_active=True)
    db.add_all([base_unit, purchase_unit])
    db.commit()

    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        base_unit_id=base_unit.id,
        unit="pcs",
        stock_quantity=100
    )
    db.add(item)
    db.commit()

    # Try to create conversion with factor 0
    response = client.post(
        "/api/item-conversions",
        json={
            "item_id": item.id,
            "purchase_unit_id": purchase_unit.id,
            "conversion_factor": 0
        },
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert response.status_code == 422  # Validation error

def test_duplicate_conversion_rejected(client, staff_token, db):
    """Test that duplicate conversions are rejected"""
    # Create units and item
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    purchase_unit = models.Unit(name="box", abbreviation="box", is_active=True)
    db.add_all([base_unit, purchase_unit])
    db.commit()

    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        base_unit_id=base_unit.id,
        unit="pcs",
        stock_quantity=100
    )
    db.add(item)
    db.commit()

    # Create first conversion
    client.post(
        "/api/item-conversions",
        json={
            "item_id": item.id,
            "purchase_unit_id": purchase_unit.id,
            "conversion_factor": 12
        },
        headers={"Authorization": f"Bearer {staff_token}"}
    )

    # Try to create duplicate
    response = client.post(
        "/api/item-conversions",
        json={
            "item_id": item.id,
            "purchase_unit_id": purchase_unit.id,
            "conversion_factor": 24
        },
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert response.status_code == 409


# ============================================================
# get_conversion_factor HELPER TESTS
# ============================================================

def test_get_conversion_factor_returns_1_for_base_unit(db):
    """Test that get_conversion_factor returns 1 for base unit"""
    # Create unit and item
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    db.add(base_unit)
    db.commit()

    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        base_unit_id=base_unit.id,
        unit="pcs",
        stock_quantity=100
    )
    db.add(item)
    db.commit()

    # Get conversion factor for base unit
    factor = get_conversion_factor(db, item.id, base_unit.id)
    assert factor == 1

def test_get_conversion_factor_returns_configured_factor(db):
    """Test that get_conversion_factor returns configured factor for purchase unit"""
    # Create units and item
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    purchase_unit = models.Unit(name="box", abbreviation="box", is_active=True)
    db.add_all([base_unit, purchase_unit])
    db.commit()

    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        base_unit_id=base_unit.id,
        unit="pcs",
        stock_quantity=100
    )
    db.add(item)
    db.commit()

    # Create conversion
    conversion = models.ItemUnitConversion(
        item_id=item.id,
        purchase_unit_id=purchase_unit.id,
        conversion_factor=12
    )
    db.add(conversion)
    db.commit()

    # Get conversion factor
    factor = get_conversion_factor(db, item.id, purchase_unit.id)
    assert factor == 12

def test_get_conversion_factor_raises_error_for_unknown_unit(db):
    """Test that get_conversion_factor raises error for unit without conversion"""
    from fastapi import HTTPException

    # Create units and item
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    other_unit = models.Unit(name="box", abbreviation="box", is_active=True)
    db.add_all([base_unit, other_unit])
    db.commit()

    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        base_unit_id=base_unit.id,
        unit="pcs",
        stock_quantity=100
    )
    db.add(item)
    db.commit()

    # Try to get conversion factor for unit without conversion
    with pytest.raises(HTTPException) as exc_info:
        get_conversion_factor(db, item.id, other_unit.id)
    assert exc_info.value.status_code == 400


# ============================================================
# DATA PRESERVATION TESTS
# ============================================================

def test_existing_stock_quantities_preserved(db):
    """Test that existing stock quantities are not changed by Phase 2"""
    # Create item with stock
    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        unit="pcs",
        stock_quantity=50
    )
    db.add(item)
    db.commit()
    original_stock = item.stock_quantity

    # Simulate Phase 2: add base_unit_id (but don't change stock)
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    db.add(base_unit)
    db.commit()

    item.base_unit_id = base_unit.id
    db.commit()
    db.refresh(item)

    # Verify stock unchanged
    assert item.stock_quantity == original_stock

def test_old_unit_field_preserved(db):
    """Test that old 'unit' text field is still present and unchanged"""
    # Create item
    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        unit="box",
        stock_quantity=11
    )
    db.add(item)
    db.commit()
    original_unit = item.unit

    # Simulate Phase 2: add base_unit_id
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    db.add(base_unit)
    db.commit()

    item.base_unit_id = base_unit.id
    db.commit()
    db.refresh(item)

    # Verify old unit field unchanged
    assert item.unit == original_unit


# ============================================================
# INTEGRATION TESTS
# ============================================================

def test_item_can_have_base_unit_and_conversions(db):
    """Test that an item can have base_unit_id and multiple conversions"""
    # Create units
    base_unit = models.Unit(name="piece", abbreviation="pcs", is_active=True)
    box_unit = models.Unit(name="box", abbreviation="box", is_active=True)
    pack_unit = models.Unit(name="pack", abbreviation="pack", is_active=True)
    db.add_all([base_unit, box_unit, pack_unit])
    db.commit()

    # Create item
    item = models.InventoryItem(
        item_code="TEST-001",
        item_name="Test Item",
        base_unit_id=base_unit.id,
        unit="pcs",
        stock_quantity=1000
    )
    db.add(item)
    db.commit()

    # Create conversions
    conv1 = models.ItemUnitConversion(
        item_id=item.id,
        purchase_unit_id=box_unit.id,
        conversion_factor=12
    )
    conv2 = models.ItemUnitConversion(
        item_id=item.id,
        purchase_unit_id=pack_unit.id,
        conversion_factor=6
    )
    db.add_all([conv1, conv2])
    db.commit()

    # Verify relationships
    db.refresh(item)
    assert item.base_unit.name == "piece"
    assert len(item.conversions) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
