"""
Phase 6: Purchase Order Module Units - Database Migration

Adds unit conversion support to purchase_order_items table.

Changes:
1. Add ordered_unit_id (ForeignKey to units table)
2. Add conversion_factor (snapshot at PO creation time)
3. Add ordered_quantity_display (original quantity in selected unit)

Note:
- quantity_ordered continues to store BASE unit quantity (for Phase 5B compatibility)
- New columns are nullable for backward compatibility with existing PO data
"""

import sqlite3
from datetime import datetime

def migrate_phase6_po_units():
    """Add unit conversion fields to purchase_order_items table"""

    conn = sqlite3.connect('school_stock.db')
    cursor = conn.cursor()

    print("=" * 70)
    print("Phase 6: Purchase Order Module Units - Database Migration")
    print("=" * 70)

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(purchase_order_items)")
    columns = [row[1] for row in cursor.fetchall()]

    print("\nCurrent purchase_order_items columns:")
    for col in columns:
        print(f"  - {col}")

    # Add ordered_unit_id column if it doesn't exist
    if 'ordered_unit_id' not in columns:
        print("\n[1/3] Adding ordered_unit_id column...")
        cursor.execute("""
            ALTER TABLE purchase_order_items
            ADD COLUMN ordered_unit_id INTEGER REFERENCES units(id)
        """)
        print("  [OK] ordered_unit_id column added")
    else:
        print("\n[1/3] ordered_unit_id column already exists")

    # Add conversion_factor column if it doesn't exist
    if 'conversion_factor' not in columns:
        print("\n[2/3] Adding conversion_factor column...")
        cursor.execute("""
            ALTER TABLE purchase_order_items
            ADD COLUMN conversion_factor INTEGER
        """)
        print("  [OK] conversion_factor column added")
    else:
        print("\n[2/3] conversion_factor column already exists")

    # Add ordered_quantity_display column if it doesn't exist
    if 'ordered_quantity_display' not in columns:
        print("\n[3/3] Adding ordered_quantity_display column...")
        cursor.execute("""
            ALTER TABLE purchase_order_items
            ADD COLUMN ordered_quantity_display INTEGER
        """)
        print("  [OK] ordered_quantity_display column added")
    else:
        print("\n[3/3] ordered_quantity_display column already exists")

    conn.commit()

    # Verify migration
    print("\n" + "=" * 70)
    print("Verifying Migration")
    print("=" * 70)

    cursor.execute("PRAGMA table_info(purchase_order_items)")
    columns_after = [row[1] for row in cursor.fetchall()]

    required_columns = ['ordered_unit_id', 'conversion_factor', 'ordered_quantity_display']
    all_present = all(col in columns_after for col in required_columns)

    if all_present:
        print("\n[SUCCESS] All required columns present:")
        for col in required_columns:
            print(f"  ✓ {col}")

        # Show sample data structure
        print("\nUpdated purchase_order_items table structure:")
        cursor.execute("PRAGMA table_info(purchase_order_items)")
        for row in cursor.fetchall():
            col_id, name, col_type, not_null, default, pk = row
            nullable = "NOT NULL" if not_null else "NULLABLE"
            print(f"  {name:30} {col_type:15} {nullable}")
    else:
        print("\n[ERROR] Migration incomplete!")
        missing = [col for col in required_columns if col not in columns_after]
        print(f"Missing columns: {missing}")
        conn.close()
        return False

    conn.close()

    print("\n" + "=" * 70)
    print("Phase 6 Database Migration: COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Update models.py - Add fields to PurchaseOrderItem model")
    print("2. Update schemas.py - Add unit fields to PO schemas")
    print("3. Update crud.py - Add unit conversion logic to PO create/update")
    print("4. Update frontend - Add unit dropdown and conversion preview")
    print("")

    return True

if __name__ == "__main__":
    try:
        success = migrate_phase6_po_units()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
