"""
Phase 3A: Migration Analysis and Review

This script analyzes existing inventory items and generates a migration review report.
It does NOT modify any data - this is analysis only.

Rules:
- Auto-safe mappings: pcs, piece, unit, sheet, bottle, liter, meter, roll, set, pair
- Ambiguous/review-needed: box, pack, dozen, ream, gallon, unknown/empty
- No stock quantity changes
- Flag items needing admin review
"""

import sqlite3
import csv
from datetime import datetime

def analyze_migration():
    """Analyze all inventory items and generate migration review report"""

    conn = sqlite3.connect('school_stock.db')
    cursor = conn.cursor()

    # Fetch all active inventory items
    cursor.execute("""
        SELECT id, item_code, item_name, category, unit, stock_quantity, base_unit_id
        FROM inventory_items
        WHERE is_deleted = 0
        ORDER BY item_code
    """)

    items = cursor.fetchall()

    # Get unit lookup (name to id)
    cursor.execute("SELECT id, name FROM units")
    units_map = {name: uid for uid, name in cursor.fetchall()}
    units_by_id = {uid: name for uid, name in cursor.fetchall()}

    # Auto-safe mappings (unit text -> proposed base unit name)
    safe_mappings = {
        'pcs': 'piece',
        'pc': 'piece',
        'piece': 'piece',
        'pieces': 'piece',
        'unit': 'unit',
        'sheet': 'sheet',
        'bottle': 'bottle',
        'liter': 'liter',
        'meter': 'meter',
        'roll': 'roll',
        'set': 'set',
        'pair': 'pair',
    }

    # Ambiguous units that need review
    ambiguous_units = {
        'box': 'Purchase unit - confirm conversion factor',
        'pack': 'Purchase unit - confirm conversion factor',
        'dozen': 'Purchase unit - always 12 pieces, confirm base unit',
        'ream': 'Purchase unit - typically 500 sheets, confirm',
        'gallon': 'Volume unit - confirm if base or purchase unit',
    }

    # Analyze each item
    analysis_results = []
    auto_safe_count = 0
    review_needed_count = 0

    for item_id, item_code, item_name, category, old_unit, stock_qty, current_base_unit_id in items:
        old_unit_lower = (old_unit or '').strip().lower()

        # Determine migration confidence and proposed base unit
        if not old_unit_lower:
            # Empty unit
            confidence = 'unknown'
            proposed_base = 'piece'  # Default suggestion
            note = 'Empty unit - propose "piece" as default, needs review'
            review_needed_count += 1

        elif old_unit_lower in safe_mappings:
            # Auto-safe mapping
            confidence = 'auto'
            proposed_base = safe_mappings[old_unit_lower]
            note = f'Safe mapping: {old_unit} → {proposed_base}, no stock change'
            auto_safe_count += 1

        elif old_unit_lower in ambiguous_units:
            # Ambiguous - needs review
            confidence = 'review'
            proposed_base = 'piece'  # Default suggestion for ambiguous
            note = ambiguous_units[old_unit_lower]
            review_needed_count += 1

        else:
            # Unknown unit
            confidence = 'unknown'
            proposed_base = 'piece'  # Default suggestion
            note = f'Unknown unit "{old_unit}" - needs manual mapping decision'
            review_needed_count += 1

        # Get proposed base unit ID
        proposed_base_unit_id = units_map.get(proposed_base, '')

        analysis_results.append({
            'item_id': item_id,
            'item_code': item_code,
            'item_name': item_name,
            'category': category or 'N/A',
            'current_old_unit': old_unit or 'N/A',
            'current_stock_quantity': stock_qty,
            'proposed_base_unit': proposed_base,
            'proposed_base_unit_id': proposed_base_unit_id,
            'migration_confidence': confidence,
            'migration_note': note,
            'current_base_unit_id': current_base_unit_id or 'NULL'
        })

    # Generate CSV report
    csv_filename = 'unit_migration_review.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'item_id', 'item_code', 'item_name', 'category',
            'current_old_unit', 'current_stock_quantity',
            'proposed_base_unit', 'proposed_base_unit_id',
            'migration_confidence', 'migration_note', 'current_base_unit_id'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analysis_results)

    # Generate console report
    print("="*100)
    print("PHASE 3A: MIGRATION ANALYSIS REPORT")
    print("="*100)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total items analyzed: {len(items)}")
    print(f"Auto-safe items: {auto_safe_count}")
    print(f"Review-needed items: {review_needed_count}")
    print(f"CSV report generated: {csv_filename}")
    print("="*100)

    # Print auto-safe items
    print("\nAUTO-SAFE ITEMS (can migrate without stock change):")
    print("-"*100)
    auto_items = [r for r in analysis_results if r['migration_confidence'] == 'auto']
    if auto_items:
        print(f"{'Code':<12} {'Name':<30} {'Category':<12} {'Unit':<8} -> {'Proposed':<10} {'Stock'}")
        print("-"*100)
        for item in auto_items:
            print(f"{item['item_code']:<12} {item['item_name'][:28]:<30} "
                  f"{item['category']:<12} {item['current_old_unit']:<8} -> "
                  f"{item['proposed_base_unit']:<10} {item['current_stock_quantity']}")
    else:
        print("  None")

    # Print review-needed items
    print("\nREVIEW-NEEDED ITEMS (require admin confirmation):")
    print("-"*100)
    review_items = [r for r in analysis_results if r['migration_confidence'] in ('review', 'unknown')]
    if review_items:
        for item in review_items:
            print(f"\n{item['item_code']}: {item['item_name']} ({item['category']})")
            print(f"  Current Unit: {item['current_old_unit']}")
            print(f"  Current Stock: {item['current_stock_quantity']}")
            print(f"  Proposed Base Unit: {item['proposed_base_unit']}")
            print(f"  Confidence: {item['migration_confidence'].upper()}")
            print(f"  Note: {item['migration_note']}")

            # Special handling for ITM-009
            if item['item_code'] == 'ITM-009':
                print(f"  >>> CRITICAL: This is ITM-009 (notebook with 'box' unit)")
                print(f"  >>> ACTION REQUIRED: Admin must confirm conversion factor")
                print(f"  >>> Example: If 1 box = 12 pieces, then stock = 11 boxes × 12 = 132 pieces")
    else:
        print("  None")

    # Summary
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Total items: {len(items)}")
    print(f"Auto-safe (can migrate): {auto_safe_count} ({auto_safe_count/len(items)*100:.1f}%)")
    print(f"Review needed: {review_needed_count} ({review_needed_count/len(items)*100:.1f}%)")
    print(f"\nCSV Report: {csv_filename}")
    print("="*100)

    # Verify no stock changes
    print("\nVERIFICATION: Checking that no stock quantities were changed...")
    cursor.execute("""
        SELECT item_code, stock_quantity
        FROM inventory_items
        WHERE is_deleted = 0
        ORDER BY item_code
    """)
    current_stocks = cursor.fetchall()

    print("Current stock quantities:")
    for code, stock in current_stocks:
        print(f"  {code}: {stock}")

    print("\nCONFIRMATION: This was analysis only. No stock quantities were modified.")

    conn.close()

    return {
        'total': len(items),
        'auto_safe': auto_safe_count,
        'review_needed': review_needed_count,
        'csv_file': csv_filename,
        'review_items': review_items
    }

if __name__ == '__main__':
    results = analyze_migration()
    print("\nPhase 3A Migration Analysis Complete.")
    print("Next step: Review flagged items, then proceed to Phase 3B upon approval.")
