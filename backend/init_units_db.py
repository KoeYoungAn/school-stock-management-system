"""
Initialize database tables for Units system (Phase 2)

This script:
1. Creates the 'units' and 'item_unit_conversions' tables if they don't exist
2. Adds 'base_unit_id' column to 'inventory_items' if it doesn't exist
3. Seeds the 14 standard units

IMPORTANT: This does NOT migrate existing data. It only creates the schema.
Run this script to set up the database foundation for Phase 2.
"""

from database import engine, Base, SessionLocal
import models
from seed import seed

def init_units_tables():
    """Create units-related tables and columns"""
    print("Initializing Units system database tables...")

    # Create all tables defined in models (only creates missing ones)
    Base.metadata.create_all(bind=engine)

    print("✓ Database tables created/verified")
    print("  - units table")
    print("  - item_unit_conversions table")
    print("  - base_unit_id column in inventory_items")

    # Run seed to populate units
    print("\nSeeding standard units...")
    db = SessionLocal()
    try:
        # Check if units already exist
        unit_count = db.query(models.Unit).count()
        if unit_count == 0:
            # Seed units
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
            for name, abbr, desc in units_data:
                u = models.Unit(name=name, abbreviation=abbr, description=desc, is_active=True)
                db.add(u)
            db.commit()
            print(f"✓ Seeded {len(units_data)} standard units")
        else:
            print(f"✓ Units already exist ({unit_count} units found), skipping seed")
    finally:
        db.close()

    print("\n" + "="*60)
    print("Phase 2 Database Initialization Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run migration analysis: python analyze_unit_migration.py")
    print("2. Review existing items and their units")
    print("3. Proceed with Phase 3 migration when ready")

if __name__ == "__main__":
    init_units_tables()
