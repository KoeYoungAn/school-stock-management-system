"""
Phase 7 Migration: Add unit conversion support to Assignments and Returns

This migration adds unit conversion fields to:
1. assign_items table - for tracking assignment unit context
2. returns table - for tracking return unit context

Core principle: Stock quantities (quantity, quantity_returned) remain in BASE units.
Display quantities and conversion context are stored separately for transparency.
"""

import sqlite3
from datetime import datetime

DB_PATH = "school_stock.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("PHASE 7 MIGRATION: Assignments and Returns Unit Conversion Support")
    print("=" * 80)
    print()

    # 1. Add columns to assign_items table
    print("Step 1: Adding unit conversion columns to assign_items table...")

    columns_to_add_assignments = [
        ("assigned_unit_id", "INTEGER"),  # Unit selected for assignment
        ("conversion_factor", "INTEGER"),  # Snapshot of conversion at assignment time
        ("assigned_quantity_display", "INTEGER"),  # Original quantity in selected unit
    ]

    for col_name, col_type in columns_to_add_assignments:
        try:
            cursor.execute(f"ALTER TABLE assign_items ADD COLUMN {col_name} {col_type}")
            print(f"  [OK] Added column: {col_name} ({col_type})")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  [SKIP] Column already exists: {col_name}")
            else:
                raise

    print()

    # 2. Add columns to returns table
    print("Step 2: Adding unit conversion columns to returns table...")

    columns_to_add_returns = [
        ("returned_unit_id", "INTEGER"),  # Unit selected for return
        ("conversion_factor", "INTEGER"),  # Snapshot of conversion at return time
        ("returned_quantity_display", "INTEGER"),  # Original quantity in selected unit
    ]

    for col_name, col_type in columns_to_add_returns:
        try:
            cursor.execute(f"ALTER TABLE returns ADD COLUMN {col_name} {col_type}")
            print(f"  [OK] Added column: {col_name} ({col_type})")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  [SKIP] Column already exists: {col_name}")
            else:
                raise

    print()

    # 3. Verify the changes
    print("Step 3: Verifying schema changes...")

    # Check assign_items table
    cursor.execute("PRAGMA table_info(assign_items)")
    assign_cols = {row[1]: row[2] for row in cursor.fetchall()}

    print("\n  assign_items table columns:")
    required_assign_cols = ["assigned_unit_id", "conversion_factor", "assigned_quantity_display"]
    for col in required_assign_cols:
        if col in assign_cols:
            print(f"    [OK] {col}: {assign_cols[col]}")
        else:
            print(f"    [MISSING] {col}: NOT FOUND")

    # Check returns table
    cursor.execute("PRAGMA table_info(returns)")
    return_cols = {row[1]: row[2] for row in cursor.fetchall()}

    print("\n  returns table columns:")
    required_return_cols = ["returned_unit_id", "conversion_factor", "returned_quantity_display"]
    for col in required_return_cols:
        if col in return_cols:
            print(f"    [OK] {col}: {return_cols[col]}")
        else:
            print(f"    [MISSING] {col}: NOT FOUND")

    print()

    # 4. Display sample data for verification
    print("Step 4: Sample data verification...")

    cursor.execute("SELECT COUNT(*) FROM assign_items")
    assign_count = cursor.fetchone()[0]
    print(f"\n  Total assignments: {assign_count}")

    cursor.execute("SELECT COUNT(*) FROM returns")
    return_count = cursor.fetchone()[0]
    print(f"  Total returns: {return_count}")

    print()

    # Commit and close
    conn.commit()
    conn.close()

    print("=" * 80)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print()
    print("IMPORTANT NOTES:")
    print("1. assign_items.quantity continues to store BASE unit quantity")
    print("2. returns.quantity_returned continues to store BASE unit quantity")
    print("3. New fields store unit context for display and audit purposes")
    print("4. Backend CRUD must be updated to populate these fields")
    print("5. Frontend UI must be updated to support unit selection")
    print()
    print(f"Migration timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    migrate()
