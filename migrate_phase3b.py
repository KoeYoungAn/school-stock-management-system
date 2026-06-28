"""
Phase 3B: Existing Data Migration

This script migrates existing inventory items to the new units system.

SAFETY RULES:
1. Database must be backed up first
2. Only convert items with safe units automatically
3. ONLY ITM-009 (notebook) with "box" unit can be converted
4. ITM-009: 1 box = 10 pieces, stock 11 -> 110 pieces
5. DO NOT change stock quantities for safe units
6. DO NOT remove old unit field
7. DO NOT modify other modules

Admin Decision for ITM-009:
- Old unit: box
- Base Unit: piece
- Purchase Unit: box
- Conversion Factor: 1 box = 10 notebooks/pieces
- Old stock: 11 boxes
- New stock: 110 pieces
"""

import sqlite3
import shutil
from datetime import datetime

def backup_database():
    """Create a backup of the database"""
    source = 'school_stock.db'
    backup = f'school_stock.db.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

    shutil.copy2(source, backup)
    print(f"Database backed up to: {backup}")
    return backup

def execute_migration():
    """Execute the Phase 3B migration"""
    print("="*80)
    print("PHASE 3B: EXISTING DATA MIGRATION")
    print("="*80)

    conn = sqlite3.connect('school_stock.db')
    cursor = conn.cursor()

    # Step 1: Backup database
    print("\nStep 1: Creating database backup...")
    backup_file = backup_database()

    # Step 2: Verify base_unit_id column exists
    print("\nStep 2: Verifying database schema...")
    cursor.execute("PRAGMA table_info(inventory_items)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'base_unit_id' not in columns:
        print("ERROR: base_unit_id column not found. Run Phase 2 first.")
        return False
    print("Verified: base_unit_id column exists")

    # Step 3: Get current inventory state
    print("\nStep 3: Current inventory state (BEFORE migration):")
    cursor.execute("""
        SELECT id, item_code, item_name, category, unit, stock_quantity, base_unit_id
        FROM inventory_items WHERE is_deleted = 0 ORDER BY item_code
    """)
    items_before = cursor.fetchall()
    for item in items_before:
        item_id, code, name, category, unit, stock, base_unit = item
        print(f"  {code}: {name} | unit='{unit}' | stock={stock} | base_unit_id={base_unit}")

    # Step 4: Get unit IDs
    cursor.execute("SELECT id, name FROM units")
    units = {name: uid for uid, name in cursor.fetchall()}
    print(f"\nUnit IDs available: {units}")

    # Step 5: Get pending conversions for ITM-009
    cursor.execute("""
        SELECT item_id, purchase_unit_id, conversion_factor
        FROM item_unit_conversions
    """)
    existing_conversions = cursor.fetchall()
    print(f"\nExisting conversions: {existing_conversions}")

    # Step 6: Dry-run preview
    print("\n" + "="*80)
    print("DRY-RUN MIGRATION PREVIEW")
    print("="*80)

    preview_items = []

    for item_id, item_code, item_name, category, unit, stock, base_unit in items_before:
        unit_lower = (unit or '').strip().lower()
        old_stock = stock

        if unit_lower in ['pcs', 'pc', 'piece', 'pieces']:
            # Auto-safe: just set base_unit_id, no stock change
            new_base_unit = 'piece'
            new_stock = stock
            preview_items.append({
                'code': item_code, 'name': item_name, 'category': category,
                'old_unit': unit, 'new_base_unit': new_base_unit,
                'old_stock': old_stock, 'new_stock': new_stock,
                'conversion_needed': False
            })

        elif unit_lower == 'box':
            # ITM-009 only - based on admin approval
            if item_code == 'ITM-009':
                new_base_unit = 'piece'
                new_stock = 110  # 11 boxes * 10 pieces per box
                conversion_needed = True
                preview_items.append({
                    'code': item_code, 'name': item_name, 'category': category,
                    'old_unit': unit, 'new_base_unit': new_base_unit,
                    'old_stock': old_stock, 'new_stock': new_stock,
                    'conversion_needed': conversion_needed
                })
            else:
                # Other box items stay for review
                preview_items.append({
                    'code': item_code, 'name': item_name, 'category': category,
                    'old_unit': unit, 'new_base_unit': None,
                    'old_stock': old_stock, 'new_stock': old_stock,
                    'conversion_needed': False, 'status': 'REVIEW_NEEDED'
                })

        elif unit_lower in ['unit', 'sheet', 'bottle', 'liter', 'meter', 'roll', 'set', 'pair']:
            # Auto-safe units
            new_base_unit = unit_lower
            new_stock = stock
            preview_items.append({
                'code': item_code, 'name': item_name, 'category': category,
                'old_unit': unit, 'new_base_unit': new_base_unit,
                'old_stock': old_stock, 'new_stock': new_stock,
                'conversion_needed': False
            })
        else:
            # Unknown units
            preview_items.append({
                'code': item_code, 'name': item_name, 'category': category,
                'old_unit': unit, 'new_base_unit': None,
                'old_stock': old_stock, 'new_stock': old_stock,
                'conversion_needed': False, 'status': 'UNKNOWN_UNIT'
            })

    # Show preview
    print("\nMIGRATION PREVIEW:")
    print("-"*80)
    for item in preview_items:
        if 'status' in item and item['status'] in ('REVIEW_NEEDED', 'UNKNOWN_UNIT'):
            print(f"  {item['code']}: {item['name']} - [{item['status']}]")
        else:
            print(f"  {item['code']}: {item['old_unit']} -> {item['new_base_unit']} | "
                  f"stock: {item['old_stock']} -> {item['new_stock']}"
                  f"{' + CONVERSION' if item.get('conversion_needed') else ''}")

    # Step 7: Confirm before executing
    print("\n" + "="*80)
    print("MIGRATION CONFIRMATION")
    print("="*80)
    print("\nThis migration will:")
    print("  - Set base_unit_id for 8 auto-safe items")
    print("  - Convert ITM-009: box -> piece (stock: 11 -> 110)")
    print("  - Create conversion for ITM-009: box = 10 pieces")
    print("  - Keep old 'unit' field intact")
    print("\nItems that will NOT be converted (need admin approval):")
    print("  - None currently (only ITM-009 is ambiguous and approved)")

    confirm = input("\nProceed with migration? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Migration cancelled.")
        return False

    # Step 8: Execute migration
    print("\n" + "="*80)
    print("EXECUTING MIGRATION")
    print("="*80)

    # Auto-safe mappings
    safe_mappings = {
        'pcs': 'piece', 'pc': 'piece', 'piece': 'piece', 'pieces': 'piece',
        'unit': 'unit', 'sheet': 'sheet', 'bottle': 'bottle', 'liter': 'liter',
        'meter': 'meter', 'roll': 'roll', 'set': 'set', 'pair': 'pair'
    }

    for item_id, item_code, item_name, category, unit, stock, base_unit in items_before:
        unit_lower = (unit or '').strip().lower()

        if unit_lower in safe_mappings and unit_lower not in ['box']:
            # Auto-safe migration: set base_unit_id only, no stock change
            proposed_base = safe_mappings[unit_lower]
            base_unit_id = units.get(proposed_base)

            cursor.execute(
                "UPDATE inventory_items SET base_unit_id = ? WHERE id = ?",
                (base_unit_id, item_id)
            )
            print(f"  {item_code}: Set base_unit_id = {proposed_base} (stock unchanged: {stock})")

        elif item_code == 'ITM-009' and unit_lower == 'box':
            # ITM-009 migration based on admin approval
            # 1. Update base_unit_id to piece
            base_unit_id = units.get('piece')
            cursor.execute(
                "UPDATE inventory_items SET base_unit_id = ? WHERE id = ?",
                (base_unit_id, item_id)
            )

            # 2. Update stock quantity: 11 boxes * 10 = 110 pieces
            new_stock = 110
            cursor.execute(
                "UPDATE inventory_items SET stock_quantity = ? WHERE id = ?",
                (new_stock, item_id)
            )

            # 3. Create item_unit_conversion: 1 box = 10 pieces
            purchase_unit_id = units.get('box')
            cursor.execute(
                """INSERT INTO item_unit_conversions
                   (item_id, purchase_unit_id, conversion_factor, is_default_purchase_unit, created_at, updated_at)
                   VALUES (?, ?, 10, 1, datetime('now'), datetime('now'))""",
                (item_id, purchase_unit_id)
            )

            print(f"  {item_code}: base_unit_id = piece, stock = {stock} -> {new_stock}")
            print(f"  {item_code}: Created conversion: box = 10 pieces")

        else:
            print(f"  {item_code}: Skipped (unit='{unit}')")

    # Commit changes
    conn.commit()

    # Step 9: Verify migration
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)

    cursor.execute("""
        SELECT id, item_code, item_name, unit, stock_quantity, base_unit_id
        FROM inventory_items WHERE is_deleted = 0 ORDER BY item_code
    """)
    items_after = cursor.fetchall()

    print("\nMIGRATION VERIFICATION (AFTER migration):")
    print("-"*80)
    for item in items_after:
        item_id, code, name, unit, stock, base_unit = item
        print(f"  {code}: unit='{unit}' | stock={stock} | base_unit_id={base_unit}")

    # Verify ITM-009 specifically
    cursor.execute("SELECT stock_quantity, base_unit_id FROM inventory_items WHERE item_code = 'ITM-009'")
    itm009 = cursor.fetchone()
    if itm009 and itm009[0] == 110 and itm009[1] == units.get('piece'):
        print("\n  ITM-009: VERIFIED - stock=110, base_unit_id=piece")
    else:
        print(f"\n  ITM-009: WARNING - stock={itm009[0] if itm009 else 'None'}, base_unit_id={itm009[1] if itm009 else 'None'}")

    # Verify conversions for ITM-009
    cursor.execute("""
        SELECT ic.conversion_factor, u.name as purchase_unit
        FROM item_unit_conversions ic
        JOIN units u ON ic.purchase_unit_id = u.id
        WHERE ic.item_id = (SELECT id FROM inventory_items WHERE item_code = 'ITM-009')
    """)
    conversions = cursor.fetchall()
    if conversions:
        print(f"  ITM-009 conversions: {conversions}")
    else:
        print("  ITM-009: WARNING - No conversions found!")

    # Verify old unit field is preserved
    cursor.execute("PRAGMA table_info(inventory_items)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'unit' in columns:
        print("\n  VERIFIED: Old 'unit' field still exists")
    else:
        print("\n  WARNING: Old 'unit' field was removed!")

    conn.close()

    print("\n" + "="*80)
    print("MIGRATION COMPLETE")
    print("="*80)
    print(f"\nBackup saved at: {backup_file}")
    print("\nNext steps:")
    print("  1. Verify stock quantities in the application")
    print("  2. Check ITM-009 has correct conversion (box = 10 pieces)")
    print("  3. Proceed to Phase 4 only after approval")

    return True

if __name__ == '__main__':
    import os
    os.chdir('backend')
    success = execute_migration()
    exit(0 if success else 1)
