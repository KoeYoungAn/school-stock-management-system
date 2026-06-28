# Script to add Units and Conversions API endpoints to crud.py

# Read crud.py
with open('crud.py', 'r') as f:
    content = f.read()

# Define Units CRUD endpoints
units_router_code = """
# ============================================================
# UNITS
# ============================================================
units_router = APIRouter(prefix="/api/units", tags=["units"])


@units_router.get("")
def list_units(
    page: int = 1, limit: int = 100, search: str = "",
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    q = db.query(models.Unit)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.Unit.name.ilike(like), models.Unit.abbreviation.ilike(like)))
    if is_active is not None:
        q = q.filter(models.Unit.is_active == is_active)
    q = q.order_by(models.Unit.name.asc())
    items, total = paginate(q, page, limit)
    return {"items": [{
        "id": u.id, "name": u.name, "abbreviation": u.abbreviation,
        "description": u.description, "is_active": u.is_active,
        "created_at": u.created_at, "updated_at": u.updated_at,
    } for u in items], "total": total, "page": page, "limit": limit}


@units_router.post("")
def create_unit(payload: schemas.UnitCreate, db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    # Check for duplicate name
    existing = db.query(models.Unit).filter(models.Unit.name == payload.name.strip()).first()
    if existing:
        raise HTTPException(400, f"Unit with name '{payload.name}' already exists")

    u = models.Unit(**payload.dict())
    db.add(u); db.commit(); db.refresh(u)
    log_audit(db, admin.id, "create", "units", u.id, f"Created unit {u.name}")
    return {"id": u.id}


@units_router.get("/{uid}")
def get_unit(uid: int, db: Session = Depends(get_db),
             _: models.User = Depends(get_current_user)):
    u = db.query(models.Unit).filter(models.Unit.id == uid).first()
    if not u:
        raise HTTPException(404, "Unit not found")
    return {"id": u.id, "name": u.name, "abbreviation": u.abbreviation,
            "description": u.description, "is_active": u.is_active,
            "created_at": u.created_at, "updated_at": u.updated_at}


@units_router.put("/{uid}")
def update_unit(uid: int, payload: schemas.UnitUpdate,
                db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    u = db.query(models.Unit).filter(models.Unit.id == uid).first()
    if not u:
        raise HTTPException(404, "Unit not found")

    data = payload.dict(exclude_unset=True)

    # Check for duplicate name if name is being changed
    if "name" in data and data["name"] and data["name"].strip() != u.name:
        existing = db.query(models.Unit).filter(
            models.Unit.name == data["name"].strip(),
            models.Unit.id != uid
        ).first()
        if existing:
            raise HTTPException(400, f"Unit with name '{data['name']}' already exists")

    for k, v in data.items():
        setattr(u, k, v)
    db.commit()
    log_audit(db, admin.id, "update", "units", u.id, f"Updated unit {u.name}")
    return {"ok": True}


@units_router.delete("/{uid}")
def deactivate_unit(uid: int, db: Session = Depends(get_db),
                    admin: models.User = Depends(require_admin)):
    u = db.query(models.Unit).filter(models.Unit.id == uid).first()
    if not u:
        raise HTTPException(404, "Unit not found")

    # Check if unit is used as base_unit_id in any active items
    used_as_base = db.query(models.InventoryItem).filter(
        models.InventoryItem.base_unit_id == uid,
        models.InventoryItem.is_deleted == False  # noqa
    ).first()
    if used_as_base:
        raise HTTPException(409, f"Cannot deactivate unit '{u.name}'. It is used as base unit for active items.")

    # Check if unit is used in any active conversions
    used_in_conversion = db.query(models.ItemUnitConversion).filter(
        models.ItemUnitConversion.purchase_unit_id == uid
    ).first()
    if used_in_conversion:
        raise HTTPException(409, f"Cannot deactivate unit '{u.name}'. It is used in item conversions.")

    # Soft deactivate
    u.is_active = False
    db.commit()
    log_audit(db, admin.id, "deactivate", "units", u.id, f"Deactivated unit {u.name}")
    return {"ok": True}


"""

# Define Item Unit Conversions CRUD endpoints
conversions_router_code = """
# ============================================================
# ITEM UNIT CONVERSIONS
# ============================================================
conversions_router = APIRouter(prefix="/api/item-conversions", tags=["conversions"])


@conversions_router.get("/item/{item_id}")
def list_item_conversions(
    item_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    # Verify item exists
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.is_deleted == False  # noqa
    ).first()
    if not item:
        raise HTTPException(404, "Item not found")

    conversions = db.query(models.ItemUnitConversion).filter(
        models.ItemUnitConversion.item_id == item_id
    ).all()

    return {"items": [{
        "id": c.id, "item_id": c.item_id, "purchase_unit_id": c.purchase_unit_id,
        "purchase_unit_name": c.purchase_unit.name if c.purchase_unit else None,
        "conversion_factor": c.conversion_factor,
        "is_default_purchase_unit": c.is_default_purchase_unit,
        "created_at": c.created_at, "updated_at": c.updated_at,
    } for c in conversions]}


@conversions_router.post("")
def create_conversion(payload: schemas.ConversionCreate, db: Session = Depends(get_db),
                      user: models.User = Depends(require_staff)):
    # Verify item exists
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == payload.item_id,
        models.InventoryItem.is_deleted == False  # noqa
    ).first()
    if not item:
        raise HTTPException(404, "Item not found")

    # Verify purchase unit exists and is active
    purchase_unit = db.query(models.Unit).filter(models.Unit.id == payload.purchase_unit_id).first()
    if not purchase_unit:
        raise HTTPException(404, "Purchase unit not found")
    if not purchase_unit.is_active:
        raise HTTPException(400, f"Unit '{purchase_unit.name}' is not active")

    # Check if conversion already exists for this item and unit
    existing = db.query(models.ItemUnitConversion).filter(
        models.ItemUnitConversion.item_id == payload.item_id,
        models.ItemUnitConversion.purchase_unit_id == payload.purchase_unit_id
    ).first()
    if existing:
        raise HTTPException(409, f"Conversion for unit '{purchase_unit.name}' already exists for this item")

    # Validate conversion factor
    if payload.conversion_factor <= 0:
        raise HTTPException(400, "Conversion factor must be greater than 0")

    c = models.ItemUnitConversion(**payload.dict())
    db.add(c); db.commit(); db.refresh(c)
    log_audit(db, user.id, "create", "item_conversions", c.id,
              f"Created conversion for item {item.item_code}: 1 {purchase_unit.name} = {c.conversion_factor} base units")
    return {"id": c.id}


@conversions_router.get("/{cid}")
def get_conversion(cid: int, db: Session = Depends(get_db),
                   _: models.User = Depends(get_current_user)):
    c = db.query(models.ItemUnitConversion).filter(models.ItemUnitConversion.id == cid).first()
    if not c:
        raise HTTPException(404, "Conversion not found")
    return {"id": c.id, "item_id": c.item_id, "purchase_unit_id": c.purchase_unit_id,
            "purchase_unit_name": c.purchase_unit.name if c.purchase_unit else None,
            "conversion_factor": c.conversion_factor,
            "is_default_purchase_unit": c.is_default_purchase_unit,
            "created_at": c.created_at, "updated_at": c.updated_at}


@conversions_router.put("/{cid}")
def update_conversion(cid: int, payload: schemas.ConversionUpdate,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(require_staff)):
    c = db.query(models.ItemUnitConversion).filter(models.ItemUnitConversion.id == cid).first()
    if not c:
        raise HTTPException(404, "Conversion not found")

    data = payload.dict(exclude_unset=True)

    # Validate conversion factor if provided
    if "conversion_factor" in data and data["conversion_factor"] <= 0:
        raise HTTPException(400, "Conversion factor must be greater than 0")

    # Check if purchase_unit_id is being changed and if it would create a duplicate
    if "purchase_unit_id" in data and data["purchase_unit_id"] != c.purchase_unit_id:
        existing = db.query(models.ItemUnitConversion).filter(
            models.ItemUnitConversion.item_id == c.item_id,
            models.ItemUnitConversion.purchase_unit_id == data["purchase_unit_id"],
            models.ItemUnitConversion.id != cid
        ).first()
        if existing:
            raise HTTPException(409, "Conversion for this unit already exists for this item")

    for k, v in data.items():
        setattr(c, k, v)
    db.commit()
    log_audit(db, user.id, "update", "item_conversions", c.id, f"Updated conversion {c.id}")
    return {"ok": True}


@conversions_router.delete("/{cid}")
def delete_conversion(cid: int, db: Session = Depends(get_db),
                      user: models.User = Depends(require_staff)):
    c = db.query(models.ItemUnitConversion).filter(models.ItemUnitConversion.id == cid).first()
    if not c:
        raise HTTPException(404, "Conversion not found")

    db.delete(c); db.commit()
    log_audit(db, user.id, "delete", "item_conversions", cid, f"Deleted conversion {cid}")
    return {"ok": True}


"""

# Find position to insert units_router (after dep_router, before inv_router)
inv_router_marker = '# ============================================================\n# INVENTORY\n# ============================================================\ninv_router = APIRouter(prefix="/api/inventory", tags=["inventory"])'
inv_router_pos = content.find(inv_router_marker)

if inv_router_pos == -1:
    print("ERROR: Could not find inventory router marker")
    exit(1)

# Insert units_router before inventory router
content = content[:inv_router_pos] + units_router_code + '\n' + content[inv_router_pos:]

# Find position to insert conversions_router (after inv_router section, before asn_router)
asn_router_marker = '# ============================================================\n# ASSIGNMENTS\n# ============================================================\nasn_router = APIRouter(prefix="/api/assignments", tags=["assignments"])'
asn_router_pos = content.find(asn_router_marker)

if asn_router_pos == -1:
    print("ERROR: Could not find assignments router marker")
    exit(1)

# Insert conversions_router before assignments router
content = content[:asn_router_pos] + conversions_router_code + '\n' + content[asn_router_pos:]

# Update ALL_ROUTERS list to include new routers
# Find ALL_ROUTERS definition
old_all_routers = '    users_router, profile_router, sup_router, dep_router, inv_router,'
new_all_routers = '    users_router, profile_router, sup_router, dep_router, units_router, inv_router, conversions_router,'

if old_all_routers in content:
    content = content.replace(old_all_routers, new_all_routers)
else:
    print("WARNING: Could not find exact ALL_ROUTERS pattern, may need manual addition")

# Write the updated content
with open('crud.py', 'w') as f:
    f.write(content)

print("SUCCESS: Updated crud.py")
print("- Added units_router with CRUD endpoints")
print("- Added conversions_router with CRUD endpoints")
print("- Updated ALL_ROUTERS list")

# Count lines
line_count = len(content.split('\n'))
print(f"Total lines in crud.py: {line_count}")
