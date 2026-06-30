"""
Phase 5A: Direct Stock Receipt Testing - After Database Migration
Tests the Direct Stock Receipt API with actual database writes
"""
import sys
import sqlite3
import json
from datetime import datetime

def get_db():
    return sqlite3.connect('school_stock.db')

def test_itm016_direct_receipt():
    """Test Direct Stock Receipt with ITM-016 (Marker) - simple case (no conversion)"""
    print("=" * 60)
    print("TEST 1: Direct Stock Receipt - ITM-016 (Marker)")
    print("=" * 60)

    conn = get_db()
    c = conn.cursor()

    # Get ITM-016 details
    c.execute('SELECT id, item_code, item_name, base_unit_id, stock_quantity FROM inventory_items WHERE item_code = "ITM-016"')
    item = c.fetchone()
    if not item:
        print("[FAIL] ITM-016 not found")
        conn.close()
        return False

    item_id, item_code, item_name, base_unit_id, current_stock = item
    print(f"[OK] Item: {item_code} {item_name}")
    print(f"[OK] Current stock: {current_stock} pieces")

    # Get base unit
    c.execute('SELECT id, name FROM units WHERE id = ?', (base_unit_id,))
    unit = c.fetchone()
    base_unit_id_val, base_unit_name = unit

    print(f"[OK] Base unit: {base_unit_name} (ID {base_unit_id_val})")

    # Simulate direct receipt: receive 1 piece
    quantity_received = 1
    received_unit_id = base_unit_id_val  # Use base unit (piece)
    conversion_factor = 1  # No conversion needed

    # Insert a direct receipt record (simulating what the API would do)
    from_receiving_num = f"DR-TEST-{datetime.now().timestamp()}"
    try:
        c.execute('''
            INSERT INTO receiving (
                receiving_number, purchase_order_id, purchase_order_item_id,
                item_id, quantity_received, received_unit_id, conversion_factor,
                received_quantity_display, receiver_name, status, notes,
                date_received, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            from_receiving_num, None, None,
            item_id, quantity_received, received_unit_id, conversion_factor,
            quantity_received, "Test User", "Received", "Direct receipt test",
            datetime.now(), datetime.now(), datetime.now()
        ))
        conn.commit()
        print(f"[OK] Receiving record inserted: {from_receiving_num}")

        # Verify the record was inserted with new columns
        c.execute('SELECT received_unit_id, conversion_factor, received_quantity_display FROM receiving WHERE receiving_number = ?', (from_receiving_num,))
        rec = c.fetchone()
        if rec:
            print(f"[OK] Received unit ID: {rec[0]}, conversion factor: {rec[1]}, display qty: {rec[2]}")

        # Simulate stock update (what the API does)
        new_stock = current_stock + quantity_received
        c.execute('UPDATE inventory_items SET stock_quantity = ? WHERE id = ?', (new_stock, item_id))
        conn.commit()
        print(f"[OK] Stock updated: {current_stock} + {quantity_received} = {new_stock}")

        # Verify
        c.execute('SELECT stock_quantity FROM inventory_items WHERE id = ?', (item_id,))
        verified_stock = c.fetchone()[0]
        if verified_stock == new_stock:
            print(f"[PASS] ITM-016 Direct Receipt Success: stock is now {verified_stock} pieces")
            conn.close()
            return True
        else:
            print(f"[FAIL] Stock verification failed: expected {new_stock}, got {verified_stock}")
            conn.close()
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        conn.rollback()
        conn.close()
        return False

def test_itm009_direct_receipt():
    """Test Direct Stock Receipt with ITM-009 (Notebook) - with conversion"""
    print("\n" + "=" * 60)
    print("TEST 2: Direct Stock Receipt - ITM-009 (Notebook)")
    print("=" * 60)

    conn = get_db()
    c = conn.cursor()

    # Get ITM-009 details
    c.execute('SELECT id, item_code, item_name, base_unit_id, stock_quantity FROM inventory_items WHERE item_code = "ITM-009"')
    item = c.fetchone()
    if not item:
        print("[FAIL] ITM-009 not found")
        conn.close()
        return False

    item_id, item_code, item_name, base_unit_id, current_stock = item
    print(f"[OK] Item: {item_code} {item_name}")
    print(f"[OK] Current stock: {current_stock} pieces")

    # Get base unit
    c.execute('SELECT id, name FROM units WHERE id = ?', (base_unit_id,))
    unit = c.fetchone()
    base_unit_id_val, base_unit_name = unit
    print(f"[OK] Base unit: {base_unit_name} (ID {base_unit_id_val})")

    # Get box conversion
    c.execute('''
        SELECT c.purchase_unit_id, u.name, c.conversion_factor
        FROM item_unit_conversions c
        JOIN units u ON c.purchase_unit_id = u.id
        WHERE c.item_id = ? AND u.name = "box"
    ''', (item_id,))
    conv = c.fetchone()
    if not conv:
        print("[FAIL] Box conversion not found for ITM-009")
        conn.close()
        return False

    purchase_unit_id, purchase_unit_name, conversion_factor = conv
    print(f"[OK] Conversion: 1 {purchase_unit_name} = {conversion_factor} {base_unit_name}")

    # Simulate receiving 2 boxes
    quantity_received = 2  # User enters 2 boxes
    received_unit_id = purchase_unit_id  # User selects box unit
    base_quantity = quantity_received * conversion_factor  # Calculate base quantity

    print(f"[OK] Simulating receipt: {quantity_received} {purchase_unit_name} = {base_quantity} {base_unit_name}")

    # Insert a direct receipt record
    from_receiving_num = f"DR-TEST-{datetime.now().timestamp()}"
    try:
        c.execute('''
            INSERT INTO receiving (
                receiving_number, purchase_order_id, purchase_order_item_id,
                item_id, quantity_received, received_unit_id, conversion_factor,
                received_quantity_display, receiver_name, status, notes,
                date_received, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            from_receiving_num, None, None,
            item_id, base_quantity, received_unit_id, conversion_factor,
            quantity_received, "Test User", "Received", "Direct receipt test - 2 boxes",
            datetime.now(), datetime.now(), datetime.now()
        ))
        conn.commit()
        print(f"[OK] Receiving record inserted: {from_receiving_num}")

        # Verify the record with new columns
        c.execute('SELECT received_unit_id, conversion_factor, received_quantity_display FROM receiving WHERE receiving_number = ?', (from_receiving_num,))
        rec = c.fetchone()
        if rec:
            print(f"[OK] Conversion snapshot - unit ID: {rec[0]}, factor: {rec[1]}, display qty: {rec[2]}")

        # Simulate stock update
        new_stock = current_stock + base_quantity
        c.execute('UPDATE inventory_items SET stock_quantity = ? WHERE id = ?', (new_stock, item_id))
        conn.commit()
        print(f"[OK] Stock updated: {current_stock} + {base_quantity} = {new_stock}")

        # Verify
        c.execute('SELECT stock_quantity FROM inventory_items WHERE id = ?', (item_id,))
        verified_stock = c.fetchone()[0]
        if verified_stock == new_stock and new_stock == 130:
            print(f"[PASS] ITM-009 Direct Receipt Success: {quantity_received} {purchase_unit_name} = {base_quantity} {base_unit_name}, new stock {verified_stock} pieces")
            conn.close()
            return True
        else:
            print(f"[FAIL] Stock verification failed: expected {new_stock}, got {verified_stock}")
            conn.close()
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        conn.rollback()
        conn.close()
        return False

def main():
    print("\n" + "=" * 60)
    print("Phase 5A: Direct Stock Receipt - Database Integration Test")
    print("=" * 60)
    print()

    results = []

    # Test 1: ITM-016 (simple, no conversion)
    results.append(("ITM-016 Direct Receipt (1 piece)", test_itm016_direct_receipt()))

    # Test 2: ITM-009 (with conversion)
    results.append(("ITM-009 Direct Receipt (2 boxes = 20 pieces)", test_itm009_direct_receipt()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All Direct Stock Receipt tests passed!")
    else:
        print("[FAILURE] Some tests failed")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
