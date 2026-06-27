import sys
sys.path.insert(0, r"D:\IT year 4 final project\school-stock-management-system - Copy (4)\backend")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
import schemas
from crud import create_direct_receipt

# In-memory DB
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Setup dummy user
user = models.User(email="admin@example.com", role="Admin", full_name="Admin", password_hash="hash")
db.add(user)
db.commit()

# Setup dummy item
item = models.InventoryItem(item_code="ITM-999", item_name="Test Item", stock_quantity=10)
db.add(item)
db.commit()

print("--- Test: Direct Stock Receipt ---")
payload = schemas.DirectReceiptCreate(
    item_id=item.id,
    quantity=5,
    source="Donation",
    reason="Emergency Receipt",
    receiver_name="Admin",
    notes="Direct receipt test"
)

response = create_direct_receipt(payload, db, user)
db.refresh(item)

print(f"New Stock: {item.stock_quantity}")
assert item.stock_quantity == 15, "Inventory should be 15 (10 + 5)"

# Check movement
from models import StockMovement
mv = db.query(StockMovement).filter(StockMovement.item_id == item.id).first()
print(f"Movement Source Type: {mv.source_type}")
assert mv.source_type == "DIRECT_RECEIPT", "Movement type should be DIRECT_RECEIPT"

print("DIRECT RECEIPT TEST PASSED")
db.close()
