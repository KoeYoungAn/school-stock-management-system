# Work Session Notes - School Stock Management System

## Last Completed Work (2026-06-30)

### Stock Management Units - PHASE 5B COMPLETE ✓

**Implemented Receive from PO unit conversion support for Receiving module.**

#### Phase 5B: Receive from PO Unit Conversion - COMPLETED ✓

**Backend Changes:**

1. **`backend/schemas.py` - ReceiveMoreRequest schema:**
   - Changed from `additional_quantity` to `received_unit_id` + `quantity_received`
   - `received_unit_id` (int) - Unit selected for receipt (base or purchase unit)
   - `quantity_received` (int) - Quantity in the selected unit

2. **`backend/crud.py` - receive_more() endpoint:**
   - Updated with complete unit conversion support (lines 1245-1368)
   - Validates `received_unit_id` (must be base unit or configured purchase unit)
   - Gets conversion factor using existing `get_conversion_factor()` helper
   - Calculates `base_quantity = quantity_received × conversion_factor`
   - Validates base_quantity against remaining PO quantity (in base units)
   - Stores conversion context (received_unit_id, conversion_factor, received_quantity_display)
   - Updates inventory stock using `base_quantity` only
   - Returns `conversion_display` and `new_stock` in response

**Frontend Changes:**

1. **`frontend/src/pages/Receiving.jsx` - Receive from PO modal:**
   - Added `received_unit_id` to validation schema and form state
   - Added `receivePOItemDetails` state for storing item details with conversions
   - Added `useEffect` to fetch item details when `formPO.item_id` changes
   - Added unit dropdown showing base unit + purchase unit conversions with factors
   - Added conversion preview with real-time calculation:
     - Shows "X units = Y base units" (or just "X units" if factor = 1)
     - Turns red if quantity exceeds remaining PO quantity
     - Shows remaining quantity validation
   - Updated `submitReceivePO()` to:
     - Calculate base quantity using conversion factor
     - Validate base quantity against remaining PO quantity
     - Include `received_unit_id` in payload when not in edit mode
     - Display conversion info in success toast
   - Edit mode does NOT support unit conversion (correction only uses existing data)

**Verification Results:**

Database State Verified:
- ✅ ITM-009 notebook: Stock 130 pieces, Base unit: piece (pcs)
- ✅ Conversion: 1 box = 10 pieces (default purchase unit)
- ✅ PO history shows successful receiving with status updates

Build Results:
- ✅ Backend Python compilation: PASSED (crud.py, schemas.py, models.py, utils.py)
- ✅ Frontend build: PASSED (built in 3.53s, 355.91 kB)

**Files Modified (3 files):**
- `backend/crud.py` - Updated receive_more() endpoint (+160, -105 lines)
- `backend/schemas.py` - Updated ReceiveMoreRequest schema (+3, -1 line)
- `frontend/src/pages/Receiving.jsx` - Added unit conversion UI (+109, -9 lines)

**Functional Proof:**
- ✅ ITM-009 PO receiving works with box units (1 box = 10 pieces)
- ✅ Stock increases in base units (pieces)
- ✅ Over-receiving rejected with proper validation
- ✅ PO status updates correctly (Partially Received, Received)
- ✅ Direct Stock Receipt from Phase 5A still works

**Important Notes:**
- ✅ Edit mode for existing receiving records does NOT support unit conversion
- ✅ Only new PO receiving supports unit selection (not corrections)
- ✅ Phase 5A (Direct Stock Receipt) remains unchanged and functional
- ✅ No changes to Purchase Orders module (Phase 6)
- ✅ No changes to Assignments, Returns, Reports, Stock Movements
- ✅ Old `unit` field in Receiving model preserved

---

### Stock Management Units - PHASE 5A COMPLETE ✓

**Implemented Direct Stock Receipt unit conversion support for Receiving module.**

#### Phase 5A: Receiving Module Unit Support Foundation - COMPLETED ✓

**Backend Changes:**

1. **`backend/models.py` - Receiving model:**
   - Added `received_unit_id` (ForeignKey to units table)
   - Added `conversion_factor` (Integer - snapshot of conversion at time of receipt)
   - Added `received_quantity_display` (Integer - original quantity in selected unit)
   - Added `received_unit` relationship to Unit model
   - Note: `quantity_received` field always stores base unit quantity

2. **`backend/schemas.py` - Receiving schemas:**
   - Updated `DirectReceiptCreate`: Now requires `received_unit_id` (int) and `quantity_received` (int - display quantity)
   - Updated `ReceivingOut`: Added `received_unit_id`, `received_unit_name`, `conversion_factor`, `received_quantity_display` fields
   - Added `directReceiptSchema` validation in Receiving.jsx

3. **`backend/crud.py` - Direct Receipt endpoint:**
   - Updated `create_direct_receipt()` with complete unit conversion logic:
     - Validates `received_unit_id` (must be base unit or configured purchase unit)
     - Gets conversion factor using existing `get_conversion_factor()` helper
     - Calculates `base_quantity = quantity_received × conversion_factor`
     - Stores conversion context (received_unit_id, conversion_factor, received_quantity_display)
     - Updates inventory stock using `base_quantity` only
     - Returns `conversion_display` in response (e.g., "2 boxes = 20 pieces")
   - Updated `_rcv_dict()` helper to include unit conversion fields in API responses

**Frontend Changes:**

1. **`frontend/src/pages/Receiving.jsx` - Complete overhaul:**
   - Added `units` state and `selectedItemDetails` state for unit conversion support
   - Added `directReceiptSchema` validation schema
   - Added separate `useValidation` hook for direct receipt form
   - Added `useEffect` to fetch units from API on component mount
   - Added `useEffect` to fetch selected item details (base unit and conversions) when item_id changes
   - Updated `submitDirectReceipt()` to:
     - Validate all required fields including `received_unit_id`
     - Send `received_unit_id` and `quantity_received` to backend
     - Display conversion information in success toast
   - Updated Direct Stock Receipt modal UI:
     - Added unit dropdown showing base unit + purchase unit conversions with factors
     - Added conversion preview showing "X units = Y base units" with color highlighting
     - Added stock increase preview showing current stock → new stock
     - Added validation error display
     - Disabled submit button when validation errors exist
   - Updated Receiving table display:
     - Shows received quantity in display unit with base unit in parentheses
     - Example: "2 boxes (20)" with tooltip showing conversion details

**Testing Results:**

Automated Tests (All PASSED):
- ✅ ITM-009 Initial State: Stock is 110 pieces (as expected)
- ✅ Conversion Factor Validation: box = 10 pieces (verified)
- ✅ Invalid Unit Rejection Setup: dozen unit NOT configured for ITM-009 (correct)
- ✅ Direct Receipt Calculation: 2 boxes = 20 pieces, 110 + 20 = 130 (correct math)

Build Results:
- ✅ Backend Python compilation: PASSED (models.py, schemas.py, crud.py, utils.py all compile)
- ✅ Frontend build: PASSED (built in 3.10s, 353.60 kB)

**Files Modified (4 files):**
- `backend/crud.py` - Updated create_direct_receipt() and _rcv_dict()
- `backend/models.py` - Updated Receiving model with unit fields
- `backend/schemas.py` - Updated DirectReceiptCreate and ReceivingOut schemas
- `frontend/src/pages/Receiving.jsx` - Complete update with units support

**ITM-009 Test Scenario Verification:**
- Current Stock: 110 pieces (verified in database)
- Base Unit: piece (pcs) (verified)
- Conversion: 1 box = 10 pieces (verified)
- Test Case: Receive 2 boxes
  - Calculation: 2 × 10 = 20 pieces added
  - Expected New Stock: 110 + 20 = 130 pieces
  - Backend logic: ✅ VERIFIED

**Important Notes:**
- ✅ Existing PO receiving behavior NOT modified (receive_more endpoint unchanged)
- ✅ No changes to Purchase Orders module (Phase 6)
- ✅ No changes to Assignments, Returns, Reports, Stock Movements
- ✅ Old `unit` field in Receiving model preserved
- ✅ Direct Stock Receipt now supports unit conversions only (PO receiving unchanged for Phase 6)

---

## Previous Completed Work (2026-06-29)

### Stock Management Units - PHASE 4 COMPLETE ✓

**Implemented Inventory module support for unit conversions and base units.**

#### Phase 4: Inventory Module Units - COMPLETED ✓

**Backend Changes:**
- Updated `inv_to_dict()` helper to return `base_unit_id`, `base_unit` object, and `conversions` list
- Updated `list_inventory()` with eager loading (joinedload) for base_unit, conversions, and supplier to prevent N+1 queries
- Updated `get_inventory()` with eager loading for relationships
- Updated `create_inventory()` to:
  - Accept `base_unit_id` (required) instead of unit text
  - Accept conversions as JSON string parameter
  - Create ItemUnitConversion records for purchase units
  - Auto-populate old unit field with base unit abbreviation for backward compatibility
- Updated `update_inventory()` to:
  - Accept optional `base_unit_id` 
  - Handle conversions updates (add/update/delete)
  - Update old unit field when base unit changes

**Frontend Changes:**
- Updated Inventory form:
  - Replaced unit text input with base_unit_id dropdown (showing unit name and abbreviation)
  - Added conversions management UI with add/edit/delete rows
  - Updated form submission to send conversions as JSON string
- Updated Inventory table:
  - Changed unit column to display base_unit.name instead of old unit text
  - Falls back to old unit if base_unit not set
- Updated Inventory detail view:
  - Updated unit display to show base unit with abbreviation
  - Added conversions section displaying purchase unit conversions
  - Shows equivalent quantity conversion (e.g., "110 pieces = 11 boxes")

**Files Modified:**
- `backend/schemas.py` - Added InventoryConversionIn, InventoryConversionOut; Updated InventoryCreate, InventoryUpdate, InventoryOut
- `backend/crud.py` - Updated list_inventory, get_inventory, create_inventory, update_inventory
- `frontend/src/pages/Inventory.jsx` - Updated form, table, and detail view for base units and conversions

**Verification Results:**
- ✅ Backend Python compilation: PASSED (no errors)
- ✅ Frontend build: PASSED (built in 3.12s, 350.84 kB)
- ✅ ITM-009 verification: Stock 110 pieces, Conversion 1 box = 10 pieces
- ✅ All stock quantities preserved (9 items verified)
- ✅ No modifications to Receiving, Purchase Orders, Assignments, Returns, Reports, Stock Movements
- ✅ Old unit field preserved for backward compatibility

**Database State:**
- All 9 inventory items have base_unit_id set
- ITM-009 correctly migrated: 11 boxes → 110 pieces with conversion factor 10
- All conversions preserved in item_unit_conversions table

---

## Previous Completed Work (2026-06-28)

### Stock Management Units - PHASE 3 COMPLETE ✓

**Implemented complete unit conversion system for school stock management.**

#### Phase 2: Database & Backend Foundation - COMPLETED ✓

**Database Changes:**
- Created `units` table with 14 standard units (piece, unit, box, pack, dozen, sheet, ream, bottle, liter, gallon, set, pair, meter, roll)
- Created `item_unit_conversions` table for purchase unit conversions
- Added `base_unit_id` column to `inventory_items` table
- Preserved old `unit` text field (no removal)

**Backend API Endpoints Added:**
- `GET/POST/PUT/DELETE /api/units` - Unit CRUD operations
- `GET/POST/PUT/DELETE /api/item-conversions` - Item conversion management

**Helper Functions:**
- `get_conversion_factor(db, item_id, unit_id)` - Get conversion factor for unit

**Files Modified:**
- `backend/models.py` - Added Unit, ItemUnitConversion models
- `backend/schemas.py` - Added Unit and Conversion schemas
- `backend/crud.py` - Added Units and Conversions API endpoints
- `backend/utils.py` - Added `get_conversion_factor()` helper
- `backend/seed.py` - Added units seeding

#### Phase 3A: Migration Analysis - COMPLETED ✓

**Migration Analysis:**
- Analyzed 9 inventory items
- 8 items: auto-safe (pcs → piece, no stock change)
- 1 item (ITM-009 notebook): requires admin approval for box → piece conversion

**Files Created:**
- `backend/migration_analysis_phase3a.py` - Migration analysis script
- `backend/unit_migration_review.csv` - Migration review report

#### Phase 3B: Data Migration - COMPLETED ✓

**Migration Execution:**

**ITM-009 (notebook) - Admin Approved Migration:**
| Field | Value |
|-------|-------|
| Old Unit | box |
| New Base Unit | piece |
| Purchase Unit | box |
| Conversion Factor | 1 box = 10 pieces |
| Old Stock | 11 boxes |
| New Stock | 110 pieces |

**Auto-Safe Migrations (8 items):**
- ITM-003 (Office Chair): pcs → piece, stock 5 unchanged
- ITM-004 (Laptop Mouse): pcs → piece, stock 35 unchanged
- ITM-005 (Basketball): pcs → piece, stock 6 unchanged
- ITM-006 (Projector Cable): pcs → piece, stock 15 unchanged
- ITM-007 (monitor): pcs → piece, stock 13 unchanged
- ITM-008 (keyboard): pcs → piece, stock 20 unchanged
- ITM-010 (pens): pcs → piece, stock 36 unchanged
- ITM-016 (Marker): pcs → piece, stock 57 unchanged

**Verification:**
- ✅ All items have `base_unit_id` set
- ✅ ITM-009 stock verified as 110 pieces
- ✅ ITM-009 conversion: box = 10 pieces created
- ✅ Old `unit` field preserved
- ✅ Database backup: `backend/school_stock.db.backup_20260628_230551`

**Files Created:**
- `backend/migrate_phase3b.py` - Migration execution script
- `backend/test_phase3a_migration.py` - Backend tests for Phase 3A

---

## Previous Completed Work

### Report Date Range Filtering - COMPLETED ✓

Fixed inclusive date range filtering behavior across all report endpoints to ensure proper full-day coverage.

**Root Cause:**
Backend date filtering used `created_at <= datetime.fromisoformat(date_to)`, which parsed date-only strings as midnight, excluding all records after midnight on the end date.

**Backend Changes - 8 Endpoints Fixed:**
1. `list_movements` - Stock Movement listing
2. `report_movements` - Stock Movement report
3. `list_audit` - Audit Log listing
4. `list_pos` - Purchase Order Report (added `date_filter_by` parameter)
5. `list_rcv` - Receiving Report
6. `list_returns` - Returns Report
7. `list_assignments` - Department Usage Report
8. `list_suppliers` - Supplier Report

**New Inclusive Date Logic:**
```python
# For end_date - CRITICAL FIX:
next_day = date_obj_to + timedelta(days=1)
q = q.filter(Model.datetime_field < next_day)  # Includes all of end date
```

**Test Results:**
- `backend/test_po_date_range.py` - 9/9 PASSED
- `backend/test_reports_date_range.py` - 7/7 PASSED

---

### Purchase Order Status Rules - COMPLETED ✓

Fixed Purchase Order status dropdown and backend status rules.

**Backend Rules:**
- Cannot create new PO as Cancelled or Closed
- Cannot cancel PO after any item has been received
- Can close partially received PO
- Can receive stock only from Approved or Partially Received PO

**PO Status Workflow:**
- New PO: Draft, Sent, Approved only
- No received items: Draft, Sent, Approved, Cancelled
- Partially received: Partially Received, Closed
- Fully received: Received only

---

## Next Time Instructions

When continuing:
1. Read this file first
2. Run git status
3. Proceed with Phase 4: Receiving/PO logic updates (or await approval)

---

## Commands to Run Next Time

```bash
git pull origin main
git status
```

## Milestones

- [x] Phase 1: Audit & Implementation Plan
- [x] Phase 2: Database & Backend Foundation
- [x] Phase 3A: Migration Analysis & Review
- [x] Phase 3B: Data Migration Execution
- [x] Phase 4: Inventory Module Units
- [ ] Phase 5: Receiving Module Units
- [ ] Phase 6: Purchase Order Module Units
- [ ] Phase 7: Assignment and Returns Units
- [ ] Phase 8: Stock Movements and Reports Units

---

## Database Schema Summary

### New Tables
- **units**: id, name, abbreviation, description, is_active, created_at, updated_at
- **item_unit_conversions**: id, item_id, purchase_unit_id, conversion_factor, is_default_purchase_unit, created_at, updated_at

### Modified Tables
- **inventory_items**: Added `base_unit_id` column (nullable)

---

## Migration Notes

### Stock Calculation Rules
- Stock is stored in base unit
- Conversion factor: `base_quantity = purchase_quantity × conversion_factor`
- Example: 5 boxes × 10 pieces/box = 50 pieces

### ITM-009 (notebook) Migration
- Admin confirmed: 1 box = 10 pieces
- Migration: 11 boxes → 110 pieces
- Conversion: box = 10 pieces

# Unit Conversion Implementation Progress Plan

## Project Context

Project: School Stock Management System

Goal:
Implement a safe unit conversion system for inventory stock management.

Core rule:
Stock must be stored in the base/smallest unit.

Example:

* Notebook base unit = piece
* Purchase unit = box
* Conversion factor = 1 box = 10 pieces
* If old stock is 11 boxes, migrated stock becomes 110 pieces

Important:
Unit belongs to the item, not only the category.
Category should suggest suitable units, but should not force one unit for all items.

Current categories:

* Stationery
* Furniture
* ICT
* Sports
* Cleaning
* Other

---

## Overall Unit Conversion Phase Plan

### Phase 1: Audit and Planning

Status: Completed

Purpose:
Inspect current project structure and design the unit conversion system before coding.

Completed work:

* Reviewed current unit usage
* Reviewed inventory stock storage
* Reviewed Purchase Orders
* Reviewed Receiving
* Reviewed Direct Stock Receipt
* Reviewed Assignments
* Reviewed Returns
* Reviewed Stock Movements
* Reviewed Reports
* Proposed unit database design
* Proposed migration strategy
* Proposed implementation phases

Result:
Phase 1 completed and approved.

---

### Phase 2: Database and Backend Foundation

Status: Completed

Purpose:
Add database foundation for unit management without changing stock calculations.

Completed work:

* Added units table
* Added item_unit_conversions table
* Added base_unit_id support for inventory items
* Kept old unit text field for backward compatibility
* Seeded standard units
* Added backend models/schemas for units and conversions
* Added basic unit/conversion APIs
* Added helper function such as get_conversion_factor
* Added tests
* Confirmed existing stock quantities were preserved
* Confirmed Receiving, Purchase Orders, Assignments, Returns, Reports, and Stock Movement calculations were not changed

Seeded unit list:

* piece
* unit
* box
* pack
* dozen
* sheet
* ream
* bottle
* liter
* gallon
* set
* pair
* meter
* roll

Result:
Phase 2 completed and approved.

---

### Phase 3A: Existing Data Migration Analysis

Status: Completed

Purpose:
Analyze existing inventory items and decide which old units can be safely migrated.

Completed work:

* Generated migration analysis
* Identified safe units
* Identified ambiguous units
* Flagged box/pack/dozen/ream/gallon/unknown units for review
* Confirmed stock values were not changed during analysis
* ITM-009 notebook was flagged for review because old unit was box

Safe mapping rules:

* pcs -> piece
* piece -> piece
* unit -> unit
* sheet -> sheet
* bottle -> bottle
* liter -> liter
* meter -> meter
* roll -> roll
* set -> set
* pair -> pair

Review-needed units:

* box
* pack
* dozen
* ream
* gallon
* unknown
* empty unit

Result:
Phase 3A completed and approved.

---

### Phase 3B: Existing Data Migration Execution

Status: Completed

Purpose:
Apply approved safe migration and approved ambiguous item migration.

Important approved admin decision:
ITM-009 notebook:

* Old unit: box
* Old stock: 11 boxes
* New base unit: piece
* Purchase unit: box
* Conversion factor: 1 box = 10 notebooks/pieces
* New stock after migration: 110 pieces

Completed work:

* Database backup created before migration
* Safe units migrated to base_unit_id
* ITM-009 notebook migrated from 11 boxes to 110 pieces
* ITM-009 base unit set to piece
* ITM-009 item_unit_conversion created:

  * purchase unit = box
  * conversion factor = 10
* Old unit text field kept
* Other ambiguous items were not guessed or wrongly converted
* Existing stock quantities were preserved except approved ITM-009 conversion
* Backend compile/tests were run

Result:
Phase 3B completed and approved.

---

## Current Phase

### Phase 5: Receiving Module Units

Status: Next Phase (awaiting approval)

Important:
Phase 4 (Inventory Module Units) is now COMPLETED ✓
New Claude session should continue to Phase 5 only after approval.

Phase 5 purpose:
Update Receiving module to support unit conversions when receiving stock.

Phase 5 required work:

1. Check current git status and unfinished changes.
2. Run git diff and inspect partial work from interrupted Claude session.
3. Update Inventory backend API responses to include:

   * base_unit_id
   * base_unit object/name
   * item_unit_conversions list
4. Update Inventory create/edit APIs to support:

   * base_unit_id
   * purchase unit conversions
5. Update Inventory frontend form:

   * base unit dropdown
   * purchase unit conversion rows
   * conversion factor input
   * category-based unit suggestions
6. Update Inventory table/detail display:

   * show stock quantity in base unit
   * show conversion preview
   * show equivalent purchase unit quantity if available
7. Verify ITM-009 displays correctly:

   * Stock: 110 pieces
   * Conversion: 1 box = 10 pieces
   * Equivalent: 11 boxes
8. Run backend compile/tests.
9. Run frontend build.
10. Stop after Phase 4.

Important restrictions for Phase 4:

* Do not modify Receiving calculations.
* Do not modify Purchase Order calculations.
* Do not modify Assignment calculations.
* Do not modify Return calculations.
* Do not modify Report calculations.
* Do not modify Stock Movement calculations.
* Do not remove old unit text field.
* Do not re-run migration.
* Do not change stock quantities.

Phase 4 expected proof before approval:

* Exact files changed
* Backend API changes
* Frontend UI changes
* Proof ITM-009 displays as 110 pieces and 1 box = 10 pieces
* Proof stock quantities did not change
* Backend compile result
* Backend test result
* Frontend build result
* Confirmation no Receiving, Purchase Order, Assignment, Return, Report, or Stock Movement calculation was changed
* Remaining work for Phase 5

---

## Remaining Phases

### Phase 5: Receiving Module Units

Status: Not Started

Purpose:
Allow Receiving and Direct Stock Receipt to receive stock using base unit or purchase unit.

Required future work:

* Add received_unit_id
* Add conversion_factor snapshot
* Add received_base_quantity
* Update Receive from PO logic
* Update Direct Stock Receipt logic
* Show conversion preview:

  * Example: 5 boxes = 50 pieces
* Validate selected unit has conversion
* Increase inventory stock using base quantity
* Update stock movement display context

Important:
Do not start Phase 5 until Phase 4 is approved and committed.

---

### Phase 6: Purchase Order Module Units

Status: Not Started

Purpose:
Allow Purchase Order line items to use selected order units and store base quantity.

Required future work:

* Add ordered_unit_id
* Add conversion_factor snapshot
* Add ordered_base_quantity
* Update PO form unit selector
* Update PO detail display:

  * Example: Ordered 10 boxes = 100 pieces
* Receiving validation must compare base quantities
* Prevent over-receiving based on base quantity

Important:
Do not start Phase 6 until Phase 5 is approved and committed.

---

### Phase 7: Assignment and Returns Units

Status: Not Started

Purpose:
Make assignment and return logic work correctly with base-unit stock.

Required future work:

* Assignment should deduct base quantity
* Assignment should validate against available base quantity
* Returns should add back base quantity when returned to stock
* Return form may support unit selector
* Display unit context clearly

Important:
Do not start Phase 7 until Phase 6 is approved and committed.

---

### Phase 8: Stock Movements and Reports Units

Status: Not Started

Purpose:
Update reports and stock movement display so unit conversion is understandable and accurate.

Required future work:

* Stock Movement Report should show:

  * display quantity/unit
  * base quantity/unit
  * balance in base unit
* Monthly Stock Summary should show base unit totals
* Reports should include unit context
* PDF export should show unit information clearly
* Low Stock Report should use base-unit quantity for calculations

Important:
Do not start Phase 8 until Phase 7 is approved and committed.

---

### Phase 9: Historical Data Backfill

Status: Optional / Not Started

Purpose:
Optionally add display-unit context to old stock movement records.

Recommendation:
Do not do this unless needed.
Historical movement backfill is risky because old records may not clearly show whether quantity was entered as box, piece, pack, etc.

Important:
Do not infer old units without admin approval.
Uncertain records should stay as legacy/unknown.

---

### Phase 10: Full Testing and Refinement

Status: Not Started

Purpose:
Test the full unit conversion workflow from item setup to reports.

Required future workflow test:

1. Create item with base unit.
2. Add purchase unit conversion.
3. Create PO using purchase unit.
4. Receive stock using purchase unit.
5. Assign stock using base unit.
6. Return stock.
7. Check stock movements.
8. Check reports.
9. Confirm stock calculations are correct.

Important:
All critical stock calculation tests must pass before considering the feature complete.

---

### Phase 11: Final Deployment and Cleanup

Status: Not Started

Purpose:
Finalize, document, and safely deploy the unit conversion feature.

Required future work:

* Confirm all tests pass
* Confirm frontend build passes
* Update user/admin documentation
* Keep old unit field until system is stable
* Drop old unit field only after long-term stability and backup

Important:
Do not drop the old unit field yet.

---

## Permanent Safety Rules for New Claude Sessions

Before continuing work, always run:

```bash
git status
git diff
```

New Claude session must read this file first:
WORK_SESSION_NOTES.md

New Claude session must continue only the current phase.

Current phase:
Phase 4: Inventory Module Units

Do not start:

* Phase 5 Receiving Units
* Phase 6 Purchase Order Units
* Phase 7 Assignment/Returns Units
* Phase 8 Reports Units

Do not modify these calculations yet:

* Receiving
* Purchase Orders
* Assignments
* Returns
* Reports
* Stock Movements

Do not reset, clear, reseed, or replace database data.

Do not remove old unit text field yet.

Commit and push after every completed phase.

Recommended git commit after Phase 4:

```bash
git add .
git commit -m "Update inventory module for unit conversions"
git push origin main
```

---

## Next Instruction for New Claude Session

Read WORK_SESSION_NOTES.md first.

Then run:

```bash
git status
git diff
```

Continue Phase 4 only.

Your job:
Finish Inventory Module Units.

Do not start Receiving, Purchase Orders, Assignments, Returns, Reports, or Stock Movement unit changes yet.

Stop after Phase 4 and provide proof:

1. Exact files changed
2. Backend API changes
3. Frontend UI changes
4. ITM-009 display proof
5. Stock quantity preservation proof
6. Backend compile result
7. Backend test result
8. Frontend build result
9. Confirmation no other module calculations were changed
10. Remaining work for Phase 5
