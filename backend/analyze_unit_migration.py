"""
Migration Analysis Script for Units System (Phase 2)

This script analyzes existing inventory items and their current 'unit' field values,
then proposes base_unit mappings and flags items that need manual review.

IMPORTANT: This script is READ-ONLY. It does NOT modify any data.
It only generates a migration analysis report.

Usage:
    python analyze_unit_migration.py
"""

from database import SessionLocal
import models

def analyze_migration():
    """Analyze existing inventory items and propose migration strategy"""
    db = SessionLocal()
    try:
        # Get all active inventory items
        items = db.query(models.InventoryItem).filter(
            models.InventoryItem.is_deleted == False  # noqa
        ).all()

        if len(items) == 0:
            print("No inventory items found. Nothing to analyze.")
            return

        # Get units for reference
        units = {u.name: u.id for u in db.query(models.Unit).all()}

        print("\n" + "="*80)
        print("UNIT MIGRATION ANALYSIS REPORT")
        print("="*80)
        print(f"\nTotal items to analyze: {len(items)}")
        print(f"Available units: {len(units)}")
        print("\n" + "="*80)

        # Categorize items
        auto_migrate = []
        needs_review = []

        for item in items:
            old_unit = (item.unit or "").lower().strip()

            # Mapping rules
            migration_info = {
                'item_code': item.item_code,
                'item_name': item.item_name,
                'category': item.category,
                'old_unit': item.unit,
                'old_stock': item.stock_quantity,
                'proposed_base_unit': None,
                'proposed_stock': item.stock_quantity,
                'migration_status': None,
                'migration_note': None
            }

            # Auto-migration mappings
            if old_unit in ['pcs', 'pc', 'piece', 'pieces']:
                migration_info['proposed_base_unit'] = 'piece'
                migration_info['migration_status'] = 'AUTO_MIGRATE'
                migration_info['migration_note'] = 'Direct mapping, no stock change'
                auto_migrate.append(migration_info)

            elif old_unit == 'unit':
                migration_info['proposed_base_unit'] = 'unit'
                migration_info['migration_status'] = 'AUTO_MIGRATE'
                migration_info['migration_note'] = 'Direct mapping, no stock change'
                auto_migrate.append(migration_info)

            elif old_unit == 'sheet':
                migration_info['proposed_base_unit'] = 'sheet'
                migration_info['migration_status'] = 'AUTO_MIGRATE'
                migration_info['migration_note'] = 'Direct mapping, no stock change'
                auto_migrate.append(migration_info)

            elif old_unit == 'bottle':
                migration_info['proposed_base_unit'] = 'bottle'
                migration_info['migration_status'] = 'AUTO_MIGRATE'
                migration_info['migration_note'] = 'Direct mapping, no stock change'
                auto_migrate.append(migration_info)

            elif old_unit == 'box':
                migration_info['proposed_base_unit'] = 'piece'
                migration_info['proposed_stock'] = '???'
                migration_info['migration_status'] = 'MANUAL_REVIEW_REQUIRED'
                migration_info['migration_note'] = f'Box is ambiguous. Need to determine: How many pieces per box? Current stock: {item.stock_quantity} boxes'
                needs_review.append(migration_info)

            else:
                migration_info['proposed_base_unit'] = '???'
                migration_info['proposed_stock'] = '???'
                migration_info['migration_status'] = 'UNKNOWN_UNIT'
                migration_info['migration_note'] = f'Unknown unit "{item.unit}". Needs manual mapping decision.'
                needs_review.append(migration_info)

        # Print auto-migrate items
        print("\n" + "-"*80)
        print(f"AUTO-MIGRATE ITEMS ({len(auto_migrate)} items)")
        print("-"*80)
        if auto_migrate:
            print(f"{'Code':<12} {'Name':<25} {'Category':<12} {'Old Unit':<10} → {'New Base Unit':<10} Stock")
            print("-"*80)
            for item in auto_migrate:
                print(f"{item['item_code']:<12} {item['item_name'][:24]:<25} {item['category']:<12} "
                      f"{item['old_unit']:<10} → {item['proposed_base_unit']:<10} {item['old_stock']}")
        else:
            print("None")

        # Print items needing review
        print("\n" + "-"*80)
        print(f"ITEMS REQUIRING MANUAL REVIEW ({len(needs_review)} items)")
        print("-"*80)
        if needs_review:
            for item in needs_review:
                print(f"\nItem Code: {item['item_code']}")
                print(f"  Name:          {item['item_name']}")
                print(f"  Category:      {item['category']}")
                print(f"  Old Unit:      {item['old_unit']}")
                print(f"  Current Stock: {item['old_stock']}")
                print(f"  Status:        {item['migration_status']}")
                print(f"  Note:          {item['migration_note']}")

                if item['migration_status'] == 'MANUAL_REVIEW_REQUIRED':
                    print(f"\n  RECOMMENDED ACTION:")
                    print(f"  1. Ask admin: How many pieces per {item['old_unit']}?")
                    print(f"  2. If 1 {item['old_unit']} = N pieces:")
                    print(f"     - Set base_unit = 'piece'")
                    print(f"     - Update stock: {item['old_stock']} {item['old_unit']} × N = ??? pieces")
                    print(f"     - Create conversion: 1 {item['old_unit']} = N pieces")
                    print(f"  3. If {item['old_unit']} is the base unit:")
                    print(f"     - Set base_unit = '{item['old_unit']}'")
                    print(f"     - Keep stock as {item['old_stock']}")
        else:
            print("None - all items can be auto-migrated!")

        # Summary
        print("\n" + "="*80)
        print("MIGRATION SUMMARY")
        print("="*80)
        print(f"Total items:            {len(items)}")
        print(f"Auto-migrate:           {len(auto_migrate)} ({len(auto_migrate)/len(items)*100:.1f}%)")
        print(f"Manual review required: {len(needs_review)} ({len(needs_review)/len(items)*100:.1f}%)")

        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("1. Review items flagged for MANUAL_REVIEW_REQUIRED")
        print("2. For each item, decide:")
        print("   a. What is the base unit?")
        print("   b. What is the correct stock quantity in base units?")
        print("   c. Should purchase unit conversions be created?")
        print("3. Document decisions before proceeding to Phase 3 migration")
        print("4. DO NOT execute migration until all review items are resolved")

        # Generate CSV for admin review
        csv_filename = 'migration_analysis.csv'
        with open(csv_filename, 'w') as f:
            f.write("Item Code,Item Name,Category,Old Unit,Old Stock,Proposed Base Unit,Proposed Stock,Migration Status,Notes\n")
            for item in auto_migrate + needs_review:
                f.write(f'"{item["item_code"]}","{item["item_name"]}","{item["category"]}",'
                       f'"{item["old_unit"]}",{item["old_stock"]},"{item["proposed_base_unit"]}",'
                       f'"{item["proposed_stock"]}","{item["migration_status"]}","{item["migration_note"]}"\n')

        print(f"\nCSV report generated: {csv_filename}")
        print("="*80 + "\n")

    finally:
        db.close()

if __name__ == "__main__":
    analyze_migration()
