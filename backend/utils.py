import os
import re
import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

import models

UPLOAD_DIR = "uploads"
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB


# ---------------- Password hashing ----------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${h.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, hex_hash = password_hash.split("$", 1)
    except ValueError:
        return False
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return secrets.compare_digest(h.hex(), hex_hash)


# ---------------- File uploads ----------------
def save_upload(file: UploadFile, subdir: str = "") -> str:
    if not file or not file.filename:
        raise HTTPException(400, "No file provided")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Only jpg, jpeg, png, webp files are allowed")
    contents = file.file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(400, "File exceeds 5MB limit")
    target_dir = os.path.join(UPLOAD_DIR, subdir) if subdir else UPLOAD_DIR
    os.makedirs(target_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(target_dir, fname)
    with open(path, "wb") as f:
        f.write(contents)
    rel = os.path.relpath(path, UPLOAD_DIR).replace("\\", "/")
    return rel  # store relative path under uploads/


# ---------------- Code generators ----------------
def _next_seq(db: Session, model, column, prefix: str, width: int = 3, year: Optional[int] = None) -> str:
    pattern = f"{prefix}-"
    if year is not None:
        pattern = f"{prefix}-{year}-"
    rows = db.query(column).filter(column.like(f"{pattern}%")).all()
    max_n = 0
    rx = re.compile(rf"^{re.escape(pattern)}(\d+)$")
    for (val,) in rows:
        if not val:
            continue
        m = rx.match(val)
        if m:
            n = int(m.group(1))
            if n > max_n:
                max_n = n
    return f"{pattern}{str(max_n + 1).zfill(width)}"


def gen_item_code(db: Session) -> str:
    return _next_seq(db, models.InventoryItem, models.InventoryItem.item_code, "ITM", 3)


def gen_assign_number(db: Session) -> str:
    return _next_seq(db, models.AssignItem, models.AssignItem.assign_number, "ASN", 3)


def gen_po_number(db: Session) -> str:
    return _next_seq(db, models.PurchaseOrder, models.PurchaseOrder.po_number, "PO", 3, year=datetime.utcnow().year)


def gen_receiving_number(db: Session) -> str:
    return _next_seq(db, models.Receiving, models.Receiving.receiving_number, "RCV", 3)


def gen_return_number(db: Session) -> str:
    return _next_seq(db, models.ReturnRecord, models.ReturnRecord.return_number, "RTN", 3)


# ---------------- Audit ----------------
def log_audit(db: Session, user_id: Optional[int], action: str, module: str,
              record_id: Optional[int], description: str = ""):
    entry = models.AuditLog(
        user_id=user_id, action=action, module=module,
        record_id=record_id, description=description,
    )
    db.add(entry)
    db.commit()


# ---------------- Stock movement helper ----------------
def record_movement(db: Session, item: models.InventoryItem, mtype: str,
                    quantity: int, source_type: str, source_id: Optional[int],
                    user_id: Optional[int], notes: str = ""):
    """Adjusts item.stock_quantity and writes a movement row.
    quantity is positive; mtype determines direction.
    """
    delta = quantity if mtype == "IN" else -quantity if mtype == "OUT" else quantity
    new_balance = (item.stock_quantity or 0) + delta
    if new_balance < 0:
        raise HTTPException(400, f"Stock cannot go negative for item {item.item_code}")
    item.stock_quantity = new_balance
    db.add(models.StockMovement(
        item_id=item.id, movement_type=mtype, quantity=quantity,
        balance_after=new_balance, source_type=source_type, source_id=source_id,
        notes=notes, created_by=user_id,
    ))


# ---------------- PDF report ----------------
def build_report_pdf(title: str, headers: list, rows: list, system_name: str,
                     school_name: str, logo_path: Optional[str] = None,
                     filters_summary: str = "") -> bytes:
    from io import BytesIO
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = []

    # Header
    if logo_path and os.path.exists(logo_path):
        try:
            story.append(Image(logo_path, width=60, height=60))
        except Exception:
            pass
    story.append(Paragraph(f"<b>{system_name}</b>", styles["Title"]))
    story.append(Paragraph(school_name, styles["Heading3"]))
    story.append(Paragraph(title, styles["Heading2"]))
    cambodia_tz = timezone(timedelta(hours=7))
    story.append(Paragraph(f"Generated: {datetime.now(cambodia_tz).strftime('%d/%m/%Y, %H:%M:%S')}", styles["Normal"]))
    if filters_summary:
        story.append(Paragraph(filters_summary, styles["Normal"]))
    story.append(Spacer(1, 12))

    # Table
    data = [headers] + [[str(c) if c is not None else "" for c in r] for r in rows]
    if not rows:
        data.append(["No data"] + [""] * (len(headers) - 1))
    tbl = Table(data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tbl)
    doc.build(story)
    return buf.getvalue()

# ---------------- Unit conversion helper ----------------
def get_conversion_factor(db: Session, item_id: int, unit_id: int) -> int:
    """Get conversion factor for an item's unit.
    Returns 1 if unit_id equals item's base_unit_id.
    """
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    
    if unit_id == item.base_unit_id:
        return 1
    
    conversion = db.query(models.ItemUnitConversion).filter(
        models.ItemUnitConversion.item_id == item_id,
        models.ItemUnitConversion.purchase_unit_id == unit_id
    ).first()
    
    if not conversion:
        raise HTTPException(400, f"No conversion found for this unit")
    
    return conversion.conversion_factor
