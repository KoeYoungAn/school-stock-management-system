"""
Backend tests for Phase 3A: Migration Analysis and Review

Tests verify:
- Migration analysis preserves stock values
- Box units are flagged for review
- Unknown units are flagged for review
- Safe units are mapped correctly
- No stock quantity is changed during analysis
"""

import pytest
import sqlite3
import os

# The migration analysis script connects to school_stock.db in the current directory
# We'll use the same database for testing
DB_PATH = 'backend/school_stock.db'


def test_migration_analysis_csv_generated():
    """Test that migration analysis generates CSV file"""
    # Run migration analysis
    results = analyze_migration()

    # Verify CSV file was created
    import os
    assert os.path.exists('unit_migration_review.csv'), "CSV file was not generated"
    assert results['csv_file'] == 'unit_migration_review.csv'


def test_migration_analysis_preserves_stock_values():
    """Test that migration analysis does NOT change stock quantities"""
    # Get stock quantities before analysis
    conn = sqlite3.connect('school_stock.db')
    cursor = conn.cursor()

    cursor.execute("SELECT item_code, stock_quantity FROM inventory_items WHERE is_deleted = 0")
    before_stocks = {code: stock for code, stock in cursor.fetchall()}

    conn.close()

    # Run migration analysis
    results = analyze_migration()

    # Get stock quantities after analysis
    conn = sqlite3.connect('school_stock.db')
    cursor = conn.cursor()

    cursor.execute("SELECT item_code, stock_quantity FROM inventory_items WHERE is_deleted = 0")
    after_stocks = {code: stock for code, stock in cursor.fetchall()}

    conn.close()

    # Verify stocks are unchanged
    assert before_stocks == after_stocks, "Stock quantities were changed during migration analysis"

    # Verify ITM-009 stock is still 11
    assert after_stocks.get('ITM-009') == 11, "ITM-009 stock quantity was changed"


def test_box_units_flagged_for_review():
    """Test that items with 'box' unit are flagged for review"""
    results = analyze_migration()

    # Find ITM-009 (notebook with box unit)
    review_items = results['review_items']

    it_009_found = False
    for item in review_items:
        if item['item_code'] == 'ITM-009':
            it_009_found = True
            assert item['migration_confidence'] == 'review', "ITM-009 should be flagged for review"
            assert 'box' in item['current_old_unit'].lower(), "ITM-009 should have box unit"

    assert it_009_found, "ITM-009 was not found in review items"


def test_unknown_units_flagged_for_review():
    """Test that items with unknown units are flagged for review"""
    results = analyze_migration()

    review_items = results['review_items']

    for item in review_items:
        assert item['migration_confidence'] in ('review', 'unknown'), \
            f"Item {item['item_code']} with confidence '{item['migration_confidence']}' should be flagged"


def test_safe_units_mapped_correctly():
    """Test that safe units (pcs, piece, unit, etc.) are mapped correctly"""
    results = analyze_migration()

    auto_items = [r for r in results['review_items'] if r['migration_confidence'] == 'auto']

    # Check pcs -> piece mapping
    pcs_items = [r for r in auto_items if 'pcs' in r['current_old_unit'].lower()]
    for item in pcs_items:
        assert item['proposed_base_unit'] == 'piece', \
            f"Item {item['item_code']} with unit 'pcs' should map to 'piece'"


def test_total_items_analyzed():
    """Test that correct number of items are analyzed"""
    results = analyze_migration()

    # Should analyze all active inventory items
    conn = sqlite3.connect('school_stock.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventory_items WHERE is_deleted = 0")
    expected_total = cursor.fetchone()[0]
    conn.close()

    assert results['total'] == expected_total, f"Expected {expected_total} items, got {results['total']}"


def test_no_database_changes_during_analysis():
    """Test that no database tables are modified during analysis"""
    conn = sqlite3.connect('school_stock.db')
    cursor = conn.cursor()

    # Get table list before
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables_before = cursor.fetchall()

    # Run analysis
    results = analyze_migration()

    # Get table list after
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables_after = cursor.fetchall()

    conn.close()

    # Verify tables unchanged
    assert tables_before == tables_after, "Database tables were modified during migration analysis"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
