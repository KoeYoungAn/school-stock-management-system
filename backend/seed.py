from datetime import datetime, timedelta
from database import SessionLocal
import models
from utils import hash_password


def seed():
    db = SessionLocal()
    try:
        # Seed units if they don't exist
        if db.query(models.Unit).count() == 0:
            units_data = [
                ("piece", "pcs", "Individual piece or unit"),
                ("unit", "unit", "Generic unit"),
                ("box", "box", "Box or carton"),
                ("pack", "pack", "Package or packet"),
                ("dozen", "doz", "12 units"),
                ("sheet", "sht", "Single sheet"),
                ("ream", "rm", "500 sheets (standard)"),
                ("bottle", "btl", "Bottle container"),
                ("liter", "L", "Liter volume"),
                ("gallon", "gal", "Gallon volume"),
                ("set", "set", "Complete set"),
                ("pair", "pair", "Pair of items"),
                ("meter", "m", "Meter length"),
                ("roll", "roll", "Roll"),
            ]
            units = []
            for name, abbr, desc in units_data:
                u = models.Unit(name=name, abbreviation=abbr, description=desc, is_active=True)
                db.add(u)
                units.append(u)
            db.flush()
            print(f"Seeded {len(units)} standard units.")

        if db.query(models.User).count() > 0:
            return
        # Users
        users = [
            models.User(full_name="Admin User", email="admin@school.local",
                        role="Admin", status="Active",
                        password_hash=hash_password("admin123")),
            models.User(full_name="Storekeeper One", email="storekeeper@school.local",
                        role="Storekeeper", status="Active",
                        password_hash=hash_password("store123")),
            models.User(full_name="Teacher One", email="teacher@school.local",
                        role="Teacher", status="Active",
                        password_hash=hash_password("teacher123")),
        ]
        db.add_all(users); db.flush()

        suppliers = [
            models.Supplier(supplier_name="Bright Office Supply", contact_person="Sarah",
                            email="sales@bright.local", phone="111-222", status="Active"),
            models.Supplier(supplier_name="TechHub Education", contact_person="Daniel",
                            email="info@techhub.local", phone="333-444", status="Active"),
        ]
        db.add_all(suppliers); db.flush()

        deps = [
            models.Department(department_name="Administration", department_head="Principal", status="Active"),
            models.Department(department_name="Science", department_head="Ms. Lee", status="Active"),
            models.Department(department_name="Library", department_head="Mr. Tan", status="Active"),
            models.Department(department_name="Sports", department_head="Coach Ali", status="Active"),
        ]
        db.add_all(deps); db.flush()

        items_data = [
            ("ITM-001", "A4 Copy Paper", "Stationery", 120, 50, suppliers[0].id),
            ("ITM-002", "Marker Pen", "Stationery", 20, 30, suppliers[0].id),
            ("ITM-003", "Office Chair", "Furniture", 15, 5, suppliers[0].id),
            ("ITM-004", "Laptop Mouse", "ICT", 35, 10, suppliers[1].id),
            ("ITM-005", "Basketball", "Sports", 8, 12, suppliers[0].id),
            ("ITM-006", "Projector Cable", "ICT", 12, 5, suppliers[1].id),
        ]
        items = []
        for code, name, cat, qty, mn, sup_id in items_data:
            it = models.InventoryItem(
                item_code=code, item_name=name, category=cat, unit="pcs",
                supplier_id=sup_id, stock_quantity=qty, minimum_stock=mn,
                condition="Good",
            )
            db.add(it); items.append(it)
        db.flush()
        for it in items:
            if it.stock_quantity > 0:
                db.add(models.StockMovement(
                    item_id=it.id, movement_type="IN", source_type="Manual",
                    quantity=it.stock_quantity, balance_after=it.stock_quantity,
                    notes="Initial seed", created_by=users[0].id,
                ))

        # Sample PO
        po = models.PurchaseOrder(
            po_number=f"PO-{datetime.utcnow().year}-001",
            supplier_id=suppliers[1].id,
            order_date=datetime.utcnow(),
            expected_delivery_date=datetime.utcnow() + timedelta(days=7),
            status="Draft", notes="Initial sample PO",
        )
        db.add(po); db.flush()
        db.add(models.PurchaseOrderItem(
            purchase_order_id=po.id, item_id=items[3].id, quantity_ordered=10,
        ))
        db.add(models.PurchaseOrderItem(
            purchase_order_id=po.id, item_id=items[5].id, quantity_ordered=5,
        ))

        # Settings
        db.add(models.SystemSettings(
            system_name="School Stock Management System",
            school_name="Demo School", system_logo=None,
        ))

        db.commit()
        print("Seed completed.")
    finally:
        db.close()
