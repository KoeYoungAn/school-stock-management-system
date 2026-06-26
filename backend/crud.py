"""All API routers: users, profile, suppliers, departments, inventory,
assignments, purchase orders, receiving, returns, stock movements, reports,
settings, audit logs."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from utils import (
    save_upload, hash_password, log_audit, record_movement,
    gen_item_code, gen_assign_number, gen_po_number,
    gen_receiving_number, gen_return_number, build_report_pdf,
    UPLOAD_DIR,
)
from auth import get_current_user
from permissions import require_admin, require_staff, ADMIN, STOREKEEPER, TEACHER


# ============================================================
# Helper
# ============================================================
def paginate(query, page: int, limit: int):
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, total


def stock_status(item: models.InventoryItem) -> str:
    qty = item.stock_quantity or 0
    minimum = item.minimum_stock or 0
    if qty == 0:
        return "Out of Stock"
    if qty <= minimum:
        return "Low Stock"
    return "In Stock"


def inv_to_dict(it: models.InventoryItem) -> dict:
    return {
        "id": it.id, "item_code": it.item_code, "item_name": it.item_name,
        "category": it.category, "unit": it.unit, "supplier_id": it.supplier_id,
        "supplier_name": it.supplier.supplier_name if it.supplier else None,
        "stock_quantity": it.stock_quantity, "minimum_stock": it.minimum_stock,
        "storage_location": it.storage_location, "condition": it.condition,
        "item_image": it.item_image, "notes": it.notes,
        "stock_status": stock_status(it),
        "created_at": it.created_at,
    }


# ============================================================
# USERS
# ============================================================
users_router = APIRouter(prefix="/api/users", tags=["users"])


@users_router.get("")
def list_users(
    page: int = 1, limit: int = 20, search: str = "",
    role: Optional[str] = None, status: Optional[str] = None,
    sort_by: str = "id", sort_order: str = "desc",
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    q = db.query(models.User).filter(models.User.is_deleted == False)  # noqa
    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.User.full_name.ilike(like), models.User.email.ilike(like)))
    if role:
        q = q.filter(models.User.role == role)
    if status:
        q = q.filter(models.User.status == status)
    col = getattr(models.User, sort_by, models.User.id)
    q = q.order_by(desc(col) if sort_order == "desc" else asc(col))
    items, total = paginate(q, page, limit)
    return {"items": [{
        "id": u.id, "full_name": u.full_name, "email": u.email, "phone": u.phone,
        "role": u.role, "status": u.status, "profile_photo": u.profile_photo,
        "created_at": u.created_at,
    } for u in items], "total": total, "page": page, "limit": limit}


@users_router.post("")
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    if db.query(models.User).filter(models.User.email == payload.email.lower()).first():
        raise HTTPException(400, "Email already exists")
    u = models.User(
        full_name=payload.full_name, email=payload.email.lower(),
        phone=payload.phone, role=payload.role, status=payload.status,
        password_hash=hash_password(payload.password),
    )
    db.add(u); db.commit(); db.refresh(u)
    log_audit(db, admin.id, "create", "users", u.id, f"Created user {u.email}")
    return {"id": u.id}


@users_router.get("/{uid}")
def get_user(uid: int, db: Session = Depends(get_db),
             _: models.User = Depends(require_admin)):
    u = db.query(models.User).filter(models.User.id == uid, models.User.is_deleted == False).first()  # noqa
    if not u:
        raise HTTPException(404, "User not found")
    return {"id": u.id, "full_name": u.full_name, "email": u.email, "phone": u.phone,
            "role": u.role, "status": u.status, "profile_photo": u.profile_photo}


@users_router.put("/{uid}")
def update_user(uid: int, payload: schemas.UserUpdate,
                db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    u = db.query(models.User).filter(models.User.id == uid, models.User.is_deleted == False).first()  # noqa
    if not u:
        raise HTTPException(404, "User not found")
    data = payload.dict(exclude_unset=True)
    if "email" in data and data["email"]:
        data["email"] = data["email"].lower()
        existing = db.query(models.User).filter(models.User.email == data["email"], models.User.id != uid).first()
        if existing:
            raise HTTPException(400, "Email already in use")
    # prevent demoting/deactivating only active admin
    if u.role == ADMIN and (data.get("role") not in (None, ADMIN) or data.get("status") == "Inactive"):
        active_admins = db.query(models.User).filter(
            models.User.role == ADMIN, models.User.status == "Active",
            models.User.is_deleted == False, models.User.id != uid,  # noqa
        ).count()
        if active_admins == 0:
            raise HTTPException(400, "Cannot demote/deactivate the only active Admin")
    for k, v in data.items():
        setattr(u, k, v)
    db.commit()
    log_audit(db, admin.id, "update", "users", u.id, f"Updated user {u.email}")
    return {"ok": True}


@users_router.delete("/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    u = db.query(models.User).filter(models.User.id == uid, models.User.is_deleted == False).first()  # noqa
    if not u:
        raise HTTPException(404, "User not found")
    if u.role == ADMIN:
        active_admins = db.query(models.User).filter(
            models.User.role == ADMIN, models.User.status == "Active",
            models.User.is_deleted == False, models.User.id != uid,  # noqa
        ).count()
        if active_admins == 0:
            raise HTTPException(400, "Cannot delete the only active Admin")
    u.is_deleted = True
    u.deleted_at = datetime.utcnow()
    u.deleted_by = admin.id
    db.commit()
    log_audit(db, admin.id, "delete", "users", u.id, f"Deleted user {u.email}")
    return {"ok": True}


@users_router.post("/{uid}/reset-password")
def reset_password(uid: int, payload: schemas.ResetPasswordIn,
                   db: Session = Depends(get_db),
                   admin: models.User = Depends(require_admin)):
    u = db.query(models.User).filter(models.User.id == uid).first()
    if not u:
        raise HTTPException(404, "User not found")
    u.password_hash = hash_password(payload.new_password)
    db.commit()
    log_audit(db, admin.id, "password_reset", "users", u.id, f"Reset password for {u.email}")
    return {"ok": True}


# ============================================================
# PROFILE
# ============================================================
profile_router = APIRouter(prefix="/api/profile", tags=["profile"])


@profile_router.get("")
def get_profile(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "full_name": user.full_name, "email": user.email,
            "phone": user.phone, "role": user.role, "status": user.status,
            "profile_photo": user.profile_photo}


@profile_router.put("")
async def update_profile(
    full_name: str = Form(...),
    phone: str = Form(""),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    user.full_name = full_name
    user.phone = phone
    if photo and photo.filename:
        user.profile_photo = save_upload(photo, "profiles")
    db.commit()
    log_audit(db, user.id, "update", "profile", user.id, "Updated own profile")
    return {"ok": True}


# ============================================================
# SUPPLIERS
# ============================================================
sup_router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@sup_router.get("")
def list_suppliers(page: int = 1, limit: int = 20, search: str = "",
                   status: Optional[str] = None,
                   db: Session = Depends(get_db),
                   _: models.User = Depends(get_current_user)):
    q = db.query(models.Supplier).filter(models.Supplier.is_deleted == False)  # noqa
    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.Supplier.supplier_name.ilike(like),
                         models.Supplier.contact_person.ilike(like)))
    if status:
        q = q.filter(models.Supplier.status == status)
    q = q.order_by(models.Supplier.id.desc())
    items, total = paginate(q, page, limit)
    return {"items": [{
        "id": s.id, "supplier_name": s.supplier_name, "contact_person": s.contact_person,
        "email": s.email, "phone": s.phone, "address": s.address,
        "status": s.status, "notes": s.notes,
    } for s in items], "total": total, "page": page, "limit": limit}


@sup_router.post("")
def create_supplier(payload: schemas.SupplierCreate, db: Session = Depends(get_db),
                    user: models.User = Depends(require_staff)):
    s = models.Supplier(**payload.dict())
    db.add(s); db.commit(); db.refresh(s)
    log_audit(db, user.id, "create", "suppliers", s.id, f"Created supplier {s.supplier_name}")
    return {"id": s.id}


@sup_router.get("/{sid}")
def get_supplier(sid: int, db: Session = Depends(get_db),
                 _: models.User = Depends(get_current_user)):
    s = db.query(models.Supplier).filter(models.Supplier.id == sid, models.Supplier.is_deleted == False).first()  # noqa
    if not s:
        raise HTTPException(404, "Not found")
    return {"id": s.id, "supplier_name": s.supplier_name, "contact_person": s.contact_person,
            "email": s.email, "phone": s.phone, "address": s.address,
            "status": s.status, "notes": s.notes}


@sup_router.put("/{sid}")
def update_supplier(sid: int, payload: schemas.SupplierUpdate,
                    db: Session = Depends(get_db),
                    user: models.User = Depends(require_staff)):
    s = db.query(models.Supplier).filter(models.Supplier.id == sid, models.Supplier.is_deleted == False).first()  # noqa
    if not s:
        raise HTTPException(404, "Not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    log_audit(db, user.id, "update", "suppliers", s.id, f"Updated supplier {s.supplier_name}")
    return {"ok": True}


@sup_router.delete("/{sid}")
def delete_supplier(sid: int, db: Session = Depends(get_db),
                    admin: models.User = Depends(require_admin)):
    s = db.query(models.Supplier).filter(models.Supplier.id == sid, models.Supplier.is_deleted == False).first()  # noqa
    if not s:
        raise HTTPException(404, "Not found")
    used_inv = db.query(models.InventoryItem).filter(models.InventoryItem.supplier_id == sid, models.InventoryItem.is_deleted == False).first()  # noqa
    used_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.supplier_id == sid, models.PurchaseOrder.is_deleted == False).first()  # noqa
    if used_inv or used_po:
        raise HTTPException(409, "Supplier is linked to inventory or purchase orders")
    s.is_deleted = True; s.deleted_at = datetime.utcnow(); s.deleted_by = admin.id
    db.commit()
    log_audit(db, admin.id, "delete", "suppliers", s.id, f"Deleted supplier {s.supplier_name}")
    return {"ok": True}


# ============================================================
# DEPARTMENTS
# ============================================================
dep_router = APIRouter(prefix="/api/departments", tags=["departments"])


@dep_router.get("")
def list_deps(page: int = 1, limit: int = 20, search: str = "",
              status: Optional[str] = None,
              db: Session = Depends(get_db),
              _: models.User = Depends(get_current_user)):
    q = db.query(models.Department).filter(models.Department.is_deleted == False)  # noqa
    if search:
        like = f"%{search}%"
        q = q.filter(models.Department.department_name.ilike(like))
    if status:
        q = q.filter(models.Department.status == status)
    q = q.order_by(models.Department.id.desc())
    items, total = paginate(q, page, limit)
    return {"items": [{
        "id": d.id, "department_name": d.department_name,
        "department_head": d.department_head, "room_code": d.room_code,
        "location": d.location, "status": d.status, "notes": d.notes,
    } for d in items], "total": total, "page": page, "limit": limit}


@dep_router.post("")
def create_dep(payload: schemas.DepartmentCreate, db: Session = Depends(get_db),
               user: models.User = Depends(require_staff)):
    d = models.Department(**payload.dict())
    db.add(d); db.commit(); db.refresh(d)
    log_audit(db, user.id, "create", "departments", d.id, f"Created department {d.department_name}")
    return {"id": d.id}


@dep_router.get("/{did}")
def get_dep(did: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    d = db.query(models.Department).filter(models.Department.id == did, models.Department.is_deleted == False).first()  # noqa
    if not d:
        raise HTTPException(404, "Not found")
    return {"id": d.id, "department_name": d.department_name,
            "department_head": d.department_head, "room_code": d.room_code,
            "location": d.location, "status": d.status, "notes": d.notes}


@dep_router.put("/{did}")
def update_dep(did: int, payload: schemas.DepartmentUpdate,
               db: Session = Depends(get_db),
               user: models.User = Depends(require_staff)):
    d = db.query(models.Department).filter(models.Department.id == did, models.Department.is_deleted == False).first()  # noqa
    if not d:
        raise HTTPException(404, "Not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(d, k, v)
    db.commit()
    log_audit(db, user.id, "update", "departments", d.id, f"Updated department {d.department_name}")
    return {"ok": True}


@dep_router.delete("/{did}")
def delete_dep(did: int, db: Session = Depends(get_db),
               admin: models.User = Depends(require_admin)):
    d = db.query(models.Department).filter(models.Department.id == did, models.Department.is_deleted == False).first()  # noqa
    if not d:
        raise HTTPException(404, "Not found")
    linked = db.query(models.AssignItem).filter(
        models.AssignItem.assign_type == "Department",
        models.AssignItem.reference_id == did,
    ).first()
    if linked:
        raise HTTPException(409, "Department is linked to assignments")
    d.is_deleted = True; d.deleted_at = datetime.utcnow(); d.deleted_by = admin.id
    db.commit()
    log_audit(db, admin.id, "delete", "departments", d.id, f"Deleted department {d.department_name}")
    return {"ok": True}


# ============================================================
# INVENTORY
# ============================================================
inv_router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@inv_router.get("")
def list_inventory(page: int = 1, limit: int = 20, search: str = "",
                   category: Optional[str] = None, status: Optional[str] = None,
                   sort_by: str = "id", sort_order: str = "desc",
                   db: Session = Depends(get_db),
                   _: models.User = Depends(get_current_user)):
    q = db.query(models.InventoryItem).filter(models.InventoryItem.is_deleted == False)  # noqa
    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.InventoryItem.item_name.ilike(like),
                         models.InventoryItem.item_code.ilike(like)))
    if category:
        q = q.filter(models.InventoryItem.category == category)
    col = getattr(models.InventoryItem, sort_by, models.InventoryItem.id)
    q = q.order_by(desc(col) if sort_order == "desc" else asc(col))
    items, total = paginate(q, page, limit)
    rows = [inv_to_dict(i) for i in items]
    if status in ("In Stock", "Low Stock", "Out of Stock"):
        rows = [r for r in rows if r["stock_status"] == status]
    return {"items": rows, "total": total, "page": page, "limit": limit}


@inv_router.post("")
async def create_inventory(
    item_name: str = Form(...),
    category: str = Form(""),
    unit: str = Form("pcs"),
    supplier_id: Optional[int] = Form(None),
    stock_quantity: int = Form(0),
    minimum_stock: int = Form(0),
    storage_location: str = Form(""),
    condition: str = Form("Good"),
    notes: str = Form(""),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_staff),
):
    if stock_quantity < 0 or minimum_stock < 0:
        raise HTTPException(400, "Quantity values cannot be negative")
    code = gen_item_code(db)
    img_path = save_upload(image, "items") if image and image.filename else None
    it = models.InventoryItem(
        item_code=code, item_name=item_name, category=category, unit=unit,
        supplier_id=supplier_id or None, stock_quantity=stock_quantity,
        minimum_stock=minimum_stock, storage_location=storage_location,
        condition=condition, item_image=img_path, notes=notes,
    )
    db.add(it); db.commit(); db.refresh(it)
    if stock_quantity > 0:
        record_movement(db, it, "IN", stock_quantity, "Manual", None, user.id, "Initial stock")
        db.commit()
    log_audit(db, user.id, "create", "inventory", it.id, f"Created item {it.item_code}")
    return {"id": it.id, "item_code": it.item_code}


@inv_router.get("/{iid}")
def get_inventory(iid: int, db: Session = Depends(get_db),
                  _: models.User = Depends(get_current_user)):
    it = db.query(models.InventoryItem).filter(models.InventoryItem.id == iid, models.InventoryItem.is_deleted == False).first()  # noqa
    if not it:
        raise HTTPException(404, "Not found")
    return inv_to_dict(it)


@inv_router.put("/{iid}")
async def update_inventory(
    iid: int,
    item_name: str = Form(...),
    category: str = Form(""),
    unit: str = Form("pcs"),
    supplier_id: Optional[int] = Form(None),
    minimum_stock: int = Form(0),
    storage_location: str = Form(""),
    condition: str = Form("Good"),
    notes: str = Form(""),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_staff),
):
    it = db.query(models.InventoryItem).filter(models.InventoryItem.id == iid, models.InventoryItem.is_deleted == False).first()  # noqa
    if not it:
        raise HTTPException(404, "Not found")
    if minimum_stock < 0:
        raise HTTPException(400, "Minimum stock cannot be negative")
    it.item_name = item_name; it.category = category; it.unit = unit
    it.supplier_id = supplier_id or None
    it.minimum_stock = minimum_stock
    it.storage_location = storage_location; it.condition = condition; it.notes = notes
    if image and image.filename:
        it.item_image = save_upload(image, "items")
    db.commit()
    log_audit(db, user.id, "update", "inventory", it.id, f"Updated item {it.item_code}")
    return {"ok": True}


@inv_router.delete("/{iid}")
def delete_inventory(iid: int, db: Session = Depends(get_db),
                     admin: models.User = Depends(require_admin)):
    it = db.query(models.InventoryItem).filter(models.InventoryItem.id == iid, models.InventoryItem.is_deleted == False).first()  # noqa
    if not it:
        raise HTTPException(404, "Not found")
    # Soft-delete: mark as deleted regardless of related records.
    # Related records (assignments, receiving, returns, movements) keep their
    # item_id reference for historical data — the item simply disappears from
    # the active inventory list.
    it.is_deleted = True; it.deleted_at = datetime.utcnow(); it.deleted_by = admin.id
    db.commit()
    log_audit(db, admin.id, "delete", "inventory", it.id, f"Deleted item {it.item_code}")
    return {"ok": True}


# ============================================================
# ASSIGNMENTS
# ============================================================
asn_router = APIRouter(prefix="/api/assignments", tags=["assignments"])

REDUCING = {"Assigned", "Completed"}


def _asn_dict(a: models.AssignItem) -> dict:
    return {
        "id": a.id, "assign_number": a.assign_number, "item_id": a.item_id,
        "item_name": a.item.item_name if a.item else None,
        "item_code": a.item.item_code if a.item else None,
        "quantity": a.quantity, "assign_type": a.assign_type,
        "reference_id": a.reference_id,
        "assigned_user_id": a.assigned_user_id,
        "status": a.status, "notes": a.notes,
        "assigned_date": a.assigned_date,
    }


@asn_router.get("")
def list_assignments(page: int = 1, limit: int = 20, search: str = "",
                     status: Optional[str] = None,
                     db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
    q = db.query(models.AssignItem)
    if user.role == TEACHER:
        q = q.filter(models.AssignItem.assigned_user_id == user.id)
    if search:
        like = f"%{search}%"
        q = q.filter(models.AssignItem.assign_number.ilike(like))
    if status:
        q = q.filter(models.AssignItem.status == status)
    q = q.order_by(models.AssignItem.id.desc())
    items, total = paginate(q, page, limit)
    return {"items": [_asn_dict(a) for a in items],
            "total": total, "page": page, "limit": limit}


@asn_router.post("")
def create_assignment(payload: schemas.AssignCreate,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(require_staff)):
    if payload.quantity <= 0:
        raise HTTPException(400, "Quantity must be positive")
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == payload.item_id, models.InventoryItem.is_deleted == False).first()  # noqa
    if not item:
        raise HTTPException(404, "Item not found")
    a = models.AssignItem(
        assign_number=gen_assign_number(db),
        item_id=payload.item_id, quantity=payload.quantity,
        assign_type=payload.assign_type,
        reference_id=payload.reference_id, assigned_user_id=payload.assigned_user_id,
        status=payload.status, notes=payload.notes,
    )
    db.add(a)
    if payload.status in REDUCING:
        record_movement(db, item, "OUT", payload.quantity, "Assignment", None, user.id,
                        f"Assignment {a.assign_number}")
    db.commit(); db.refresh(a)
    # update movement source_id now that we have a.id
    if payload.status in REDUCING:
        last = db.query(models.StockMovement).filter(
            models.StockMovement.source_type == "Assignment",
            models.StockMovement.source_id == None,  # noqa
            models.StockMovement.item_id == item.id,
        ).order_by(models.StockMovement.id.desc()).first()
        if last:
            last.source_id = a.id
            db.commit()
    log_audit(db, user.id, "create", "assignments", a.id, f"Created assignment {a.assign_number}")
    return {"id": a.id, "assign_number": a.assign_number}


@asn_router.get("/{aid}")
def get_assignment(aid: int, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    a = db.query(models.AssignItem).filter(models.AssignItem.id == aid).first()
    if not a:
        raise HTTPException(404, "Not found")
    if user.role == TEACHER and a.assigned_user_id != user.id:
        raise HTTPException(403, "Forbidden")
    return _asn_dict(a)


@asn_router.put("/{aid}")
def update_assignment(aid: int, payload: schemas.AssignUpdate,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(require_staff)):
    a = db.query(models.AssignItem).filter(models.AssignItem.id == aid).first()
    if not a:
        raise HTTPException(404, "Not found")
    old_item = a.item
    old_qty = a.quantity
    old_status = a.status
    # Reverse old effect
    if old_status in REDUCING:
        record_movement(db, old_item, "IN", old_qty, "Assignment", a.id, user.id,
                        f"Reverse for edit {a.assign_number}")
    # Apply new values
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(a, k, v)
    new_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == a.item_id).first()
    if a.status in REDUCING:
        record_movement(db, new_item, "OUT", a.quantity, "Assignment", a.id, user.id,
                        f"Re-apply edit {a.assign_number}")
    db.commit()
    log_audit(db, user.id, "update", "assignments", a.id, f"Updated assignment {a.assign_number}")
    return {"ok": True}


@asn_router.delete("/{aid}")
def delete_assignment(aid: int, db: Session = Depends(get_db),
                      user: models.User = Depends(require_staff)):
    a = db.query(models.AssignItem).filter(models.AssignItem.id == aid).first()
    if not a:
        raise HTTPException(404, "Not found")
    if a.status in REDUCING:
        record_movement(db, a.item, "IN", a.quantity, "Assignment", a.id, user.id,
                        f"Delete restore {a.assign_number}")
    num = a.assign_number
    db.delete(a); db.commit()
    log_audit(db, user.id, "delete", "assignments", aid, f"Deleted assignment {num}")
    return {"ok": True}


# ============================================================
# PURCHASE ORDERS
# ============================================================
po_router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


def _po_dict(po: models.PurchaseOrder) -> dict:
    items = po.items
    return {
        "id": po.id, "po_number": po.po_number, "supplier_id": po.supplier_id,
        "supplier_name": po.supplier.supplier_name if po.supplier else None,
        "order_date": po.order_date, "expected_delivery_date": po.expected_delivery_date,
        "status": po.status, "notes": po.notes, "total_items": len(items),
        "items": [{
            "id": i.id, "purchase_order_id": i.purchase_order_id, "item_id": i.item_id,
            "item_code": i.item.item_code if i.item else None,
            "item_name": i.item.item_name if i.item else None,
            "quantity_ordered": i.quantity_ordered,
            "quantity_received": i.quantity_received, "notes": i.notes,
        } for i in items],
    }


@po_router.get("")
def list_pos(page: int = 1, limit: int = 20, search: str = "",
             status: Optional[str] = None,
             db: Session = Depends(get_db),
             _: models.User = Depends(get_current_user)):
    q = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.is_deleted == False)  # noqa
    if search:
        q = q.filter(models.PurchaseOrder.po_number.ilike(f"%{search}%"))
    if status:
        q = q.filter(models.PurchaseOrder.status == status)
    q = q.order_by(models.PurchaseOrder.id.desc())
    items, total = paginate(q, page, limit)
    return {"items": [_po_dict(p) for p in items],
            "total": total, "page": page, "limit": limit}


@po_router.post("")
def create_po(payload: schemas.POCreate, db: Session = Depends(get_db),
              user: models.User = Depends(require_staff)):
    if user.role == STOREKEEPER and payload.status not in ("Draft", "Sent"):
        raise HTTPException(403, "Storekeeper can only create Draft or Sent")
    if payload.expected_delivery_date and payload.expected_delivery_date < datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0):
        # allow same day
        pass
    po = models.PurchaseOrder(
        po_number=gen_po_number(db),
        supplier_id=payload.supplier_id,
        expected_delivery_date=payload.expected_delivery_date,
        status=payload.status, notes=payload.notes,
    )
    db.add(po); db.flush()
    for it in payload.items:
        if it.quantity_ordered <= 0:
            raise HTTPException(400, "Quantity ordered must be positive")
        db.add(models.PurchaseOrderItem(
            purchase_order_id=po.id, item_id=it.item_id,
            quantity_ordered=it.quantity_ordered, notes=it.notes,
        ))
    db.commit(); db.refresh(po)
    log_audit(db, user.id, "create", "purchase_orders", po.id, f"Created PO {po.po_number}")
    return {"id": po.id, "po_number": po.po_number}


@po_router.get("/{pid}")
def get_po(pid: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == pid, models.PurchaseOrder.is_deleted == False).first()  # noqa
    if not po:
        raise HTTPException(404, "Not found")
    return _po_dict(po)


@po_router.put("/{pid}")
def update_po(pid: int, payload: schemas.POUpdate,
              db: Session = Depends(get_db),
              user: models.User = Depends(require_staff)):
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == pid, models.PurchaseOrder.is_deleted == False).first()  # noqa
    if not po:
        raise HTTPException(404, "Not found")
    if user.role == STOREKEEPER and po.status not in ("Draft", "Sent"):
        raise HTTPException(403, "Storekeeper can only edit Draft or Sent POs")
    for k, v in payload.dict(exclude_unset=True).items():
        if k == "status" and user.role == STOREKEEPER and v not in ("Draft", "Sent"):
            raise HTTPException(403, "Storekeeper cannot set this status")
        setattr(po, k, v)
    db.commit()
    log_audit(db, user.id, "update", "purchase_orders", po.id, f"Updated PO {po.po_number}")
    return {"ok": True}


@po_router.delete("/{pid}")
def delete_po(pid: int, db: Session = Depends(get_db),
              admin: models.User = Depends(require_admin)):
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == pid, models.PurchaseOrder.is_deleted == False).first()  # noqa
    if not po:
        raise HTTPException(404, "Not found")
    # Soft delete allowed even if receiving records exist; they retain reference for history
    # Commented out conflict check to allow deletion
    # used = db.query(models.Receiving).filter(models.Receiving.purchase_order_id == pid).first()
    # if used:
    #     raise HTTPException(409, "PO has receiving records")
    po.is_deleted = True; po.deleted_at = datetime.utcnow(); po.deleted_by = admin.id
    db.commit()
    log_audit(db, admin.id, "delete", "purchase_orders", po.id, f"Deleted PO {po.po_number}")
    return {"ok": True}


@po_router.put("/{pid}/approve")
def approve_po(pid: int, db: Session = Depends(get_db),
               admin: models.User = Depends(require_admin)):
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == pid, models.PurchaseOrder.is_deleted == False).first()  # noqa
    if not po:
        raise HTTPException(404, "Not found")
    po.status = "Approved"
    db.commit()
    log_audit(db, admin.id, "approve", "purchase_orders", po.id, f"Approved PO {po.po_number}")
    return {"ok": True}


# PO Items
po_items_router = APIRouter(tags=["po-items"])


@po_items_router.get("/api/purchase-orders/{pid}/items")
def list_po_items(pid: int, db: Session = Depends(get_db),
                  _: models.User = Depends(get_current_user)):
    rows = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.purchase_order_id == pid).all()
    return [{
        "id": r.id, "purchase_order_id": r.purchase_order_id, "item_id": r.item_id,
        "item_code": r.item.item_code if r.item else None,
        "item_name": r.item.item_name if r.item else None,
        "quantity_ordered": r.quantity_ordered,
        "quantity_received": r.quantity_received, "notes": r.notes,
    } for r in rows]


@po_items_router.post("/api/purchase-orders/{pid}/items")
def create_po_item(pid: int, payload: schemas.POItemCreate,
                   db: Session = Depends(get_db),
                   user: models.User = Depends(require_staff)):
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == pid, models.PurchaseOrder.is_deleted == False).first()  # noqa
    if not po:
        raise HTTPException(404, "PO not found")
    row = models.PurchaseOrderItem(
        purchase_order_id=pid, item_id=payload.item_id,
        quantity_ordered=payload.quantity_ordered, notes=payload.notes,
    )
    db.add(row); db.commit(); db.refresh(row)
    log_audit(db, user.id, "create", "po_items", row.id, f"Added item to PO {po.po_number}")
    return {"id": row.id}


@po_items_router.put("/api/purchase-order-items/{item_id}")
def update_po_item(item_id: int, payload: schemas.POItemUpdate,
                   db: Session = Depends(get_db),
                   user: models.User = Depends(require_staff)):
    row = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == item_id).first()
    if not row:
        raise HTTPException(404, "Not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    log_audit(db, user.id, "update", "po_items", row.id, "Updated PO item")
    return {"ok": True}


@po_items_router.delete("/api/purchase-order-items/{item_id}")
def delete_po_item(item_id: int, db: Session = Depends(get_db),
                   user: models.User = Depends(require_staff)):
    row = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == item_id).first()
    if not row:
        raise HTTPException(404, "Not found")
    if row.quantity_received and row.quantity_received > 0:
        raise HTTPException(409, "Cannot delete a PO item with received quantity")
    db.delete(row); db.commit()
    log_audit(db, user.id, "delete", "po_items", item_id, "Deleted PO item")
    return {"ok": True}


@po_items_router.post("/api/purchase-order-items/{poi_id}/receive-more")
def receive_more(poi_id: int, payload: schemas.ReceiveMoreRequest,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(require_staff)):
    """Add additional quantity to an existing PO item.

    This is specifically for receiving MORE items on top of what's already received.
    Creates a new receiving record, updates the PO item received quantity,
    updates inventory stock, and creates a stock movement log.
    """
    # 1. Find PO item
    poi = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == poi_id).first()
    if not poi:
        raise HTTPException(404, "Purchase order item not found")

    # 2. Validate
    if payload.additional_quantity <= 0:
        raise HTTPException(400, "Additional quantity must be positive")

    already_received = poi.quantity_received or 0
    remaining = poi.quantity_ordered - already_received
    if payload.additional_quantity > remaining:
        raise HTTPException(400, f"Cannot receive more than remaining quantity ({remaining})")

    # 3. Find item
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == poi.item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")

    # 4. Create new receiving record
    r = models.Receiving(
        receiving_number=gen_receiving_number(db),
        purchase_order_id=poi.purchase_order_id,
        purchase_order_item_id=poi_id,
        item_id=poi.item_id,
        quantity_received=payload.additional_quantity,
        receiver_name=payload.receiver_name,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(r)
    db.flush()

    # 5. Update inventory and PO item (only if status is "Received")
    if payload.status == "Received":
        # Update inventory stock and create movement log
        record_movement(db, item, "IN", payload.additional_quantity,
                        "Receiving", r.id, user.id,
                        f"Receiving additional quantity {r.receiving_number}")

        # Update PO item received quantity
        poi.quantity_received = (poi.quantity_received or 0) + payload.additional_quantity

    db.commit()

    # 6. Refresh PO status
    _refresh_po_status(db, poi.purchase_order_id)

    # 7. Audit log
    log_audit(db, user.id, "receive_more", "po_items", poi_id,
              f"Received additional {payload.additional_quantity} items for PO item {poi_id}")

    return {
        "id": r.id,
        "receiving_number": r.receiving_number,
        "new_total_received": poi.quantity_received,
        "remaining": poi.quantity_ordered - poi.quantity_received
    }


# ============================================================
# RECEIVING
# ============================================================
rcv_router = APIRouter(prefix="/api/receiving", tags=["receiving"])


def _rcv_dict(r: models.Receiving) -> dict:
    return {
        "id": r.id, "receiving_number": r.receiving_number,
        "purchase_order_id": r.purchase_order_id,
        "purchase_order_item_id": r.purchase_order_item_id,
        "item_id": r.item_id,
        "item_name": r.item.item_name if r.item else None,
        "item_code": r.item.item_code if r.item else None,
        "quantity_received": r.quantity_received, "receiver_name": r.receiver_name,
        "date_received": r.date_received, "status": r.status, "notes": r.notes,
    }


def _refresh_po_status(db: Session, po_id: Optional[int]):
    if not po_id:
        return
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not po:
        return
    items = po.items
    total_ord = sum(i.quantity_ordered for i in items) if items else 0
    total_rcv = sum(i.quantity_received or 0 for i in items) if items else 0
    if total_ord and total_rcv >= total_ord:
        po.status = "Received"
    elif total_rcv > 0:
        po.status = "Partially Received"
    db.commit()


@rcv_router.get("")
def list_rcv(page: int = 1, limit: int = 20, search: str = "",
             status: Optional[str] = None,
             db: Session = Depends(get_db),
             _: models.User = Depends(require_staff)):
    q = db.query(models.Receiving)
    if search:
        q = q.filter(models.Receiving.receiving_number.ilike(f"%{search}%"))
    if status:
        q = q.filter(models.Receiving.status == status)
    q = q.order_by(models.Receiving.id.desc())
    items, total = paginate(q, page, limit)
    return {"items": [_rcv_dict(r) for r in items],
            "total": total, "page": page, "limit": limit}


@rcv_router.post("")
def create_rcv(payload: schemas.ReceivingCreate, db: Session = Depends(get_db),
               user: models.User = Depends(require_staff)):
    if payload.quantity_received <= 0:
        raise HTTPException(400, "Quantity must be positive")

    # ENFORCE PO REQUIREMENT: Normal receiving must link to a Purchase Order
    if payload.status == "Received":
        if not payload.purchase_order_id or not payload.purchase_order_item_id:
            raise HTTPException(
                400,
                "Purchase Order is required for receiving supplier items. "
                "For opening stock, donations, or manual entries, use Direct Stock Receipt instead."
            )

    if payload.purchase_order_item_id:
        poi = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == payload.purchase_order_item_id).first()
        if not poi:
            raise HTTPException(404, "Purchase order item not found")

        # Additional validations
        if poi.purchase_order_id != payload.purchase_order_id:
            raise HTTPException(400, "PO line item does not belong to the selected Purchase Order")
        if poi.item_id != payload.item_id:
            raise HTTPException(400, "Selected item must match the PO line item")

        po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == payload.purchase_order_id).first()
        if not po:
            raise HTTPException(404, "Purchase order not found")
        if po.status not in ("Approved", "Partially Received"):
            raise HTTPException(400, f"Purchase Order must be Approved or Partially Received (current status: {po.status})")

        already_received = poi.quantity_received or 0
        remaining = poi.quantity_ordered - already_received
        if payload.quantity_received > remaining:
            raise HTTPException(400, f"Cannot receive more than remaining quantity ({remaining})")

    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == payload.item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    r = models.Receiving(
        receiving_number=gen_receiving_number(db),
        purchase_order_id=payload.purchase_order_id,
        purchase_order_item_id=payload.purchase_order_item_id,
        item_id=payload.item_id, quantity_received=payload.quantity_received,
        receiver_name=payload.receiver_name, status=payload.status, notes=payload.notes,
    )
    db.add(r); db.flush()
    if payload.status == "Received":
        record_movement(db, item, "IN", payload.quantity_received,
                        "Receiving", r.id, user.id, f"Receiving {r.receiving_number}")
        if payload.purchase_order_item_id:
            poi = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == payload.purchase_order_item_id).first()
            if poi:
                poi.quantity_received = (poi.quantity_received or 0) + payload.quantity_received
    db.commit()
    _refresh_po_status(db, payload.purchase_order_id)
    log_audit(db, user.id, "create", "receiving", r.id, f"Created receiving {r.receiving_number}")
    return {"id": r.id, "receiving_number": r.receiving_number}


@rcv_router.get("/{rid}")
def get_rcv(rid: int, db: Session = Depends(get_db),
            _: models.User = Depends(require_staff)):
    r = db.query(models.Receiving).filter(models.Receiving.id == rid).first()
    if not r:
        raise HTTPException(404, "Not found")
    return _rcv_dict(r)


@rcv_router.put("/{rid}")
def update_rcv(rid: int, payload: schemas.ReceivingUpdate,
               db: Session = Depends(get_db),
               user: models.User = Depends(require_staff)):
    r = db.query(models.Receiving).filter(models.Receiving.id == rid).first()
    if not r:
        raise HTTPException(404, "Not found")
    old_status = r.status
    old_qty = r.quantity_received
    old_poi_id = r.purchase_order_item_id
    old_po_id = r.purchase_order_id

    data = payload.dict(exclude_unset=True)
    # Reverse
    # Validate update quantity if changing PO item
    if "quantity_received" in data and r.purchase_order_item_id:
        poi = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == r.purchase_order_item_id).first()
        if poi:
            # Revert the old received amount first
            already_received = poi.quantity_received - old_qty
            remaining = poi.quantity_ordered - already_received
            if data["quantity_received"] > remaining:
                raise HTTPException(400, f"Cannot receive more than remaining quantity ({remaining})")

    if old_status == "Received":
        record_movement(db, r.item, "OUT", old_qty, "Receiving", r.id, user.id,
                        f"Reverse for edit {r.receiving_number}")
        if old_poi_id:
            poi = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == old_poi_id).first()
            if poi:
                poi.quantity_received = max(0, (poi.quantity_received or 0) - old_qty)
    for k, v in data.items():
        setattr(r, k, v)
    if r.status == "Received":
        record_movement(db, r.item, "IN", r.quantity_received, "Receiving", r.id, user.id,
                        f"Re-apply edit {r.receiving_number}")
        if r.purchase_order_item_id:
            poi = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == r.purchase_order_item_id).first()
            if poi:
                poi.quantity_received = (poi.quantity_received or 0) + r.quantity_received
    db.commit()
    _refresh_po_status(db, old_po_id)
    _refresh_po_status(db, r.purchase_order_id)
    log_audit(db, user.id, "update", "receiving", r.id, f"Updated receiving {r.receiving_number}")
    return {"ok": True}


@rcv_router.delete("/{rid}")
def delete_rcv(rid: int, db: Session = Depends(get_db),
               admin: models.User = Depends(require_admin)):
    r = db.query(models.Receiving).filter(models.Receiving.id == rid).first()
    if not r:
        raise HTTPException(404, "Not found")
    if r.status == "Received":
        record_movement(db, r.item, "OUT", r.quantity_received, "Receiving", r.id, admin.id,
                        f"Delete reverse {r.receiving_number}")
        if r.purchase_order_item_id:
            poi = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.id == r.purchase_order_item_id).first()
            if poi:
                poi.quantity_received = max(0, (poi.quantity_received or 0) - r.quantity_received)
    po_id = r.purchase_order_id
    num = r.receiving_number
    db.delete(r); db.commit()
    _refresh_po_status(db, po_id)
    log_audit(db, admin.id, "delete", "receiving", rid, f"Deleted receiving {num}")
    return {"ok": True}


# ============================================================
# DIRECT STOCK RECEIPT
# ============================================================
direct_receipt_router = APIRouter(prefix="/api/direct-receipt", tags=["direct-receipt"])


@direct_receipt_router.post("")
def create_direct_receipt(payload: schemas.DirectReceiptCreate, db: Session = Depends(get_db),
                          user: models.User = Depends(require_staff)):
    """
    Direct Stock Receipt - for opening stock, donations, emergency receipt, approved manual entry.
    Does NOT link to Purchase Orders. Creates stock movement with source_type="DIRECT_RECEIPT".
    """
    if payload.quantity <= 0:
        raise HTTPException(400, "Quantity must be positive")

    if not payload.source or not payload.source.strip():
        raise HTTPException(400, "Source is required (e.g., 'Opening Stock', 'Donation', 'Emergency')")

    if not payload.reason or not payload.reason.strip():
        raise HTTPException(400, "Reason is required (e.g., 'Initial inventory', 'Donated by...')")

    if not payload.receiver_name or not payload.receiver_name.strip():
        raise HTTPException(400, "Receiver name is required")

    # Validate item exists
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == payload.item_id,
        models.InventoryItem.is_deleted == False
    ).first()
    if not item:
        raise HTTPException(404, "Item not found")

    # Create stock movement with DIRECT_RECEIPT source type
    notes = f"Direct Receipt - Source: {payload.source}, Reason: {payload.reason}"
    if payload.notes:
        notes += f", Notes: {payload.notes}"

    record_movement(
        db, item, "IN", payload.quantity,
        "DIRECT_RECEIPT", None, user.id, notes
    )

    db.commit()

    # Create audit log
    log_audit(
        db, user.id, "direct_receipt", "inventory", item.id,
        f"Direct receipt: {payload.quantity} x {item.item_name} - {payload.source}"
    )

    return {
        "ok": True,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "quantity": payload.quantity,
        "new_stock": item.stock_quantity,
        "source": payload.source,
        "reason": payload.reason
    }


# ============================================================
# RETURNS
# ============================================================
ret_router = APIRouter(prefix="/api/returns", tags=["returns"])


def _ret_dict(r: models.ReturnRecord) -> dict:
    return {
        "id": r.id, "return_number": r.return_number, "item_id": r.item_id,
        "item_name": r.item.item_name if r.item else None,
        "item_code": r.item.item_code if r.item else None,
        "quantity_returned": r.quantity_returned, "return_reason": r.return_reason,
        "condition": r.condition, "date_returned": r.date_returned,
        "received_by": r.received_by, "notes": r.notes,
    }


@ret_router.get("")
def list_returns(page: int = 1, limit: int = 20, search: str = "",
                 db: Session = Depends(get_db),
                 _: models.User = Depends(require_staff)):
    q = db.query(models.ReturnRecord)
    if search:
        q = q.filter(models.ReturnRecord.return_number.ilike(f"%{search}%"))
    q = q.order_by(models.ReturnRecord.id.desc())
    items, total = paginate(q, page, limit)
    return {"items": [_ret_dict(r) for r in items],
            "total": total, "page": page, "limit": limit}


@ret_router.post("")
def create_return(payload: schemas.ReturnCreate, db: Session = Depends(get_db),
                  user: models.User = Depends(require_staff)):
    if payload.quantity_returned <= 0:
        raise HTTPException(400, "Quantity must be positive")
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == payload.item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    r = models.ReturnRecord(
        return_number=gen_return_number(db),
        item_id=payload.item_id, quantity_returned=payload.quantity_returned,
        return_reason=payload.return_reason, condition=payload.condition,
        received_by=payload.received_by, notes=payload.notes,
    )
    db.add(r); db.flush()
    if payload.condition == "Good":
        record_movement(db, item, "IN", payload.quantity_returned,
                        "Return", r.id, user.id, f"Return {r.return_number}")
    else:
        log_audit(db, user.id, "damaged_return", "returns", r.id,
                  f"Damaged return {r.return_number} qty={payload.quantity_returned}")
    db.commit()
    log_audit(db, user.id, "create", "returns", r.id, f"Created return {r.return_number}")
    return {"id": r.id, "return_number": r.return_number}


@ret_router.get("/{rid}")
def get_return(rid: int, db: Session = Depends(get_db),
               _: models.User = Depends(require_staff)):
    r = db.query(models.ReturnRecord).filter(models.ReturnRecord.id == rid).first()
    if not r:
        raise HTTPException(404, "Not found")
    return _ret_dict(r)


@ret_router.put("/{rid}")
def update_return(rid: int, payload: schemas.ReturnUpdate,
                  db: Session = Depends(get_db),
                  user: models.User = Depends(require_staff)):
    r = db.query(models.ReturnRecord).filter(models.ReturnRecord.id == rid).first()
    if not r:
        raise HTTPException(404, "Not found")
    if r.condition == "Good":
        record_movement(db, r.item, "OUT", r.quantity_returned, "Return", r.id, user.id,
                        f"Reverse for edit {r.return_number}")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(r, k, v)
    if r.condition == "Good":
        record_movement(db, r.item, "IN", r.quantity_returned, "Return", r.id, user.id,
                        f"Re-apply edit {r.return_number}")
    db.commit()
    log_audit(db, user.id, "update", "returns", r.id, f"Updated return {r.return_number}")
    return {"ok": True}


@ret_router.delete("/{rid}")
def delete_return(rid: int, db: Session = Depends(get_db),
                  admin: models.User = Depends(require_admin)):
    r = db.query(models.ReturnRecord).filter(models.ReturnRecord.id == rid).first()
    if not r:
        raise HTTPException(404, "Not found")
    if r.condition == "Good":
        record_movement(db, r.item, "OUT", r.quantity_returned, "Return", r.id, admin.id,
                        f"Delete reverse {r.return_number}")
    num = r.return_number
    db.delete(r); db.commit()
    log_audit(db, admin.id, "delete", "returns", rid, f"Deleted return {num}")
    return {"ok": True}


# ============================================================
# STOCK MOVEMENTS
# ============================================================
mv_router = APIRouter(prefix="/api/stock-movements", tags=["stock-movements"])


@mv_router.get("")
def list_movements(page: int = 1, limit: int = 20, search: str = "",
                   movement_type: Optional[str] = None,
                   date_from: Optional[str] = None, date_to: Optional[str] = None,
                   db: Session = Depends(get_db),
                   _: models.User = Depends(require_staff)):
    q = db.query(models.StockMovement)
    if movement_type:
        q = q.filter(models.StockMovement.movement_type == movement_type)
    if date_from:
        try:
            q = q.filter(models.StockMovement.created_at >= datetime.fromisoformat(date_from))
        except Exception:
            pass
    if date_to:
        try:
            q = q.filter(models.StockMovement.created_at <= datetime.fromisoformat(date_to))
        except Exception:
            pass
    q = q.order_by(models.StockMovement.id.desc())
    items, total = paginate(q, page, limit)
    return {"items": [{
        "id": m.id, "item_id": m.item_id,
        "item_name": m.item.item_name if m.item else None,
        "item_code": m.item.item_code if m.item else None,
        "movement_type": m.movement_type, "source_type": m.source_type,
        "source_id": m.source_id, "quantity": m.quantity,
        "balance_after": m.balance_after, "notes": m.notes,
        "created_by": m.created_by, "created_at": m.created_at,
    } for m in items], "total": total, "page": page, "limit": limit}


@mv_router.get("/{mid}")
def get_movement(mid: int, db: Session = Depends(get_db),
                 _: models.User = Depends(require_staff)):
    m = db.query(models.StockMovement).filter(models.StockMovement.id == mid).first()
    if not m:
        raise HTTPException(404, "Not found")
    return {"id": m.id, "item_id": m.item_id, "movement_type": m.movement_type,
            "quantity": m.quantity, "balance_after": m.balance_after,
            "notes": m.notes, "created_at": m.created_at}


# ============================================================
# REPORTS
# ============================================================
rep_router = APIRouter(prefix="/api/reports", tags=["reports"])


def _filtered_inventory(db, category, status):
    q = db.query(models.InventoryItem).filter(models.InventoryItem.is_deleted == False)  # noqa
    if category:
        q = q.filter(models.InventoryItem.category == category)
    rows = q.all()
    if status in ("In Stock", "Low Stock", "Out of Stock"):
        rows = [r for r in rows if stock_status(r) == status]
    return rows


@rep_router.get("/stock-summary")
def stock_summary(category: Optional[str] = None, status: Optional[str] = None,
                  db: Session = Depends(get_db),
                  _: models.User = Depends(require_staff)):
    rows = _filtered_inventory(db, category, status)
    total_items = len(rows)
    total_balance = sum(r.stock_quantity or 0 for r in rows)
    low = [r for r in rows if stock_status(r) == "Low Stock"]
    out = [r for r in rows if stock_status(r) == "Out of Stock"]
    categories = {r.category for r in rows if r.category}
    recently_updated = sorted(rows, key=lambda r: r.updated_at or r.created_at or datetime.min, reverse=True)[:5]
    return {
        "total_items": total_items,
        "total_stock_balance": total_balance,
        "low_stock_count": len(low),
        "out_of_stock_count": len(out),
        "total_categories": len(categories),
        "recently_updated_count": len(recently_updated),
        "filtered_count": total_items,
        "recently_updated_items": [inv_to_dict(r) for r in recently_updated],
        "items": [inv_to_dict(r) for r in rows],
    }


@rep_router.get("/low-stock")
def low_stock(db: Session = Depends(get_db),
              _: models.User = Depends(require_staff)):
    rows = db.query(models.InventoryItem).filter(models.InventoryItem.is_deleted == False).all()  # noqa
    low = [inv_to_dict(r) for r in rows if stock_status(r) == "Low Stock"]
    return {"items": low, "count": len(low)}


@rep_router.get("/stock-movements")
def report_movements(date_from: Optional[str] = None, date_to: Optional[str] = None,
                     movement_type: Optional[str] = None,
                     db: Session = Depends(get_db),
                     _: models.User = Depends(require_staff)):
    q = db.query(models.StockMovement)
    if movement_type:
        q = q.filter(models.StockMovement.movement_type == movement_type)
    if date_from:
        try:
            q = q.filter(models.StockMovement.created_at >= datetime.fromisoformat(date_from))
        except Exception:
            pass
    if date_to:
        try:
            q = q.filter(models.StockMovement.created_at <= datetime.fromisoformat(date_to))
        except Exception:
            pass
    rows = q.order_by(models.StockMovement.id.desc()).limit(500).all()
    return {"items": [{
        "id": m.id, "item_code": m.item.item_code if m.item else None,
        "item_name": m.item.item_name if m.item else None,
        "movement_type": m.movement_type, "quantity": m.quantity,
        "balance_after": m.balance_after, "source_type": m.source_type,
        "created_at": m.created_at,
    } for m in rows]}


@rep_router.get("/monthly-stock-summary")
def monthly_stock_summary(month: int, year: int, category: Optional[str] = None, status: Optional[str] = None,
                          db: Session = Depends(get_db), _: models.User = Depends(require_staff)):
    if not (1 <= month <= 12):
        raise HTTPException(400, "Invalid month")

    from calendar import monthrange
    import datetime
    start_date = datetime.datetime(year, month, 1)
    end_date = datetime.datetime(year, month, monthrange(year, month)[1], 23, 59, 59)

    # Base query for items
    q = db.query(models.InventoryItem).filter(models.InventoryItem.is_deleted == False)
    if category: q = q.filter(models.InventoryItem.category == category)
    items = q.all()

    results = []
    for item in items:
        # Opening and closing balances come from the movement ledger itself.
        # This keeps the report aligned with Stock Movement balance_after values,
        # including manual initial stock and edit/delete reversal movements.
        last_mv = db.query(models.StockMovement).filter(
            models.StockMovement.item_id == item.id,
            models.StockMovement.created_at < start_date
        ).order_by(models.StockMovement.created_at.desc(), models.StockMovement.id.desc()).first()
        opening = last_mv.balance_after if last_mv else 0

        mvs = db.query(models.StockMovement).filter(
            models.StockMovement.item_id == item.id,
            models.StockMovement.created_at >= start_date,
            models.StockMovement.created_at <= end_date
        ).order_by(models.StockMovement.created_at.asc(), models.StockMovement.id.asc()).all()

        rcv = sum(m.quantity for m in mvs if m.movement_type == "IN" and m.source_type == "Receiving")
        issued = sum(m.quantity for m in mvs if m.movement_type == "OUT" and m.source_type == "Assignment")
        returned = sum(m.quantity for m in mvs if m.movement_type == "IN" and m.source_type == "Return")

        if mvs:
            closing = mvs[-1].balance_after
        else:
            closing = opening

        # Reconcile everything not shown in received/issued/returned: manual stock,
        # receiving reversals, assignment reversals, and explicit adjustments.
        adj = closing - opening - rcv - returned + issued

        # Historical status based on closing balance
        closing_status = "Out of Stock" if closing <= 0 else ("Low Stock" if closing <= (item.minimum_stock or 0) else "In Stock")

        if status and closing_status != status:
            continue

        results.append({
            "id": item.id, "item_code": item.item_code, "item_name": item.item_name,
            "category": item.category, "unit": item.unit,
            "opening_balance": opening, "total_received": rcv,
            "total_issued": issued, "total_returned": returned,
            "total_adjustment": adj, "closing_balance": closing,
            "status": closing_status
        })

    return {
        "items": results,
        "metadata": {
            "month": month,
            "year": year,
            "month_name": start_date.strftime("%B"),
            "start_date": start_date.strftime("%d/%m/%Y"),
            "end_date": end_date.strftime("%d/%m/%Y"),
            "category": category,
            "status": status,
        }
    }
    settings = db.query(models.SystemSettings).first()
    sys_name = settings.system_name if settings else "School Stock Management System"
    school_name = settings.school_name if settings else "Demo School"
    logo_path = None
    if settings and settings.system_logo:
        candidate = os.path.join(UPLOAD_DIR, settings.system_logo)
        if os.path.exists(candidate):
            logo_path = candidate
    filters = []
    if category: filters.append(f"Category: {category}")
    if status: filters.append(f"Status: {status}")
    fsum = " | ".join(filters) if filters else ""

    if report == "low-stock":
        rows = db.query(models.InventoryItem).filter(models.InventoryItem.is_deleted == False).all()  # noqa
        rows = [r for r in rows if stock_status(r) == "Low Stock"]
        headers = ["Code", "Item", "Category", "Stock", "Min", "Status"]
        data = [[r.item_code, r.item_name, r.category or "", r.stock_quantity, r.minimum_stock, "Low Stock"] for r in rows]
        title = "Low Stock Report"
    elif report == "movements":
        mvs = db.query(models.StockMovement).order_by(models.StockMovement.id.desc()).limit(500).all()
        headers = ["Date", "Item", "Type", "Qty", "Balance", "Source"]
        data = [[(m.created_at + timedelta(hours=7)).strftime("%d/%m/%Y, %H:%M:%S") if m.created_at else "",
                 m.item.item_name if m.item else "", m.movement_type, m.quantity,
                 m.balance_after, m.source_type or ""] for m in mvs]
        title = "Stock Movements Report"
    else:
        rows = _filtered_inventory(db, category, status)
        headers = ["Code", "Item", "Category", "Unit", "Stock", "Min", "Status"]
        data = [[r.item_code, r.item_name, r.category or "", r.unit or "",
                 r.stock_quantity, r.minimum_stock, stock_status(r)] for r in rows]
        title = "Stock Summary Report"

    pdf = build_report_pdf(title, headers, data, sys_name, school_name, logo_path, fsum)
    log_audit(db, admin.id, "export", "reports", None, f"Exported PDF: {title}")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{report}.pdf"'})


# ============================================================
# SETTINGS
# ============================================================
set_router = APIRouter(prefix="/api/settings", tags=["settings"])


@set_router.get("")
def get_settings(db: Session = Depends(get_db),
                 _: models.User = Depends(get_current_user)):
    s = db.query(models.SystemSettings).first()
    if not s:
        s = models.SystemSettings()
        db.add(s); db.commit(); db.refresh(s)
    return {"id": s.id, "system_name": s.system_name, "school_name": s.school_name,
            "system_logo": s.system_logo}


@set_router.put("")
async def update_settings(
    system_name: str = Form(...),
    school_name: str = Form(...),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    s = db.query(models.SystemSettings).first()
    if not s:
        s = models.SystemSettings()
        db.add(s); db.flush()
    s.system_name = system_name
    s.school_name = school_name
    if logo and logo.filename:
        s.system_logo = save_upload(logo, "logos")
    db.commit()
    log_audit(db, admin.id, "update", "settings", s.id, "Updated system settings")
    return {"ok": True}


# ============================================================
# AUDIT LOGS
# ============================================================
audit_router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@audit_router.get("")
def list_audit(page: int = 1, limit: int = 20, search: str = "",
               module: Optional[str] = None, action: Optional[str] = None,
               date_from: Optional[str] = None, date_to: Optional[str] = None,
               db: Session = Depends(get_db),
               _: models.User = Depends(require_admin)):
    q = db.query(models.AuditLog)
    if module:
        q = q.filter(models.AuditLog.module == module)
    if action:
        q = q.filter(models.AuditLog.action == action)
    if search:
        q = q.filter(models.AuditLog.description.ilike(f"%{search}%"))
    if date_from:
        try:
            q = q.filter(models.AuditLog.created_at >= datetime.fromisoformat(date_from))
        except Exception:
            pass
    if date_to:
        try:
            q = q.filter(models.AuditLog.created_at <= datetime.fromisoformat(date_to))
        except Exception:
            pass
    q = q.order_by(models.AuditLog.id.desc())
    items, total = paginate(q, page, limit)
    return {"items": [{
        "id": a.id, "user_id": a.user_id,
        "user_name": a.user.full_name if a.user else None,
        "action": a.action, "module": a.module, "record_id": a.record_id,
        "description": a.description, "created_at": a.created_at,
    } for a in items], "total": total, "page": page, "limit": limit}


# ============================================================
# Aggregator
# ============================================================
ALL_ROUTERS = [
    users_router, profile_router, sup_router, dep_router, inv_router,
    asn_router, po_router, po_items_router, rcv_router, direct_receipt_router, ret_router,
    mv_router, rep_router, set_router, audit_router,
]
