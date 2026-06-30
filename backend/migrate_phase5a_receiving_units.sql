-- Phase 5A Safe Database Migration: Add Unit Conversion Support to Receiving Table
-- Purpose: Add received_unit_id, conversion_factor, received_quantity_display columns
-- Safety: Uses ALTER TABLE to add nullable columns - preserves all existing data
-- Date: 2026-06-30

-- Step 1: Add received_unit_id column (ForeignKey to units.id)
-- Nullable to preserve existing receiving records
ALTER TABLE receiving ADD COLUMN received_unit_id INTEGER DEFAULT NULL;

-- Step 2: Add conversion_factor column (snapshot of conversion at time of receipt)
-- Nullable to preserve existing receiving records
ALTER TABLE receiving ADD COLUMN conversion_factor INTEGER DEFAULT NULL;

-- Step 3: Add received_quantity_display column (original quantity in selected unit)
-- Nullable to preserve existing receiving records
ALTER TABLE receiving ADD COLUMN received_quantity_display INTEGER DEFAULT NULL;

-- Verify migration
-- SELECT * FROM pragma_table_info('receiving');
