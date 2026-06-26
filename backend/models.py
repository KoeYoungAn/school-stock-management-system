from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from database import Base


def _now():
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(50))
    role = Column(String(30), nullable=False, default="Teacher")  # Admin/Storekeeper/Teacher
    status = Column(String(20), nullable=False, default="Active")  # Active/Inactive
    profile_photo = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(150), nullable=False)
    contact_person = Column(String(150))
    email = Column(String(150))
    phone = Column(String(50))
    address = Column(Text)
    status = Column(String(20), default="Active")
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(150), nullable=False)
    department_head = Column(String(150))
    room_code = Column(String(50))
    location = Column(String(150))
    status = Column(String(20), default="Active")
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(50), unique=True, nullable=False, index=True)
    item_name = Column(String(200), nullable=False)
    category = Column(String(100))
    unit = Column(String(50), default="pcs")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    stock_quantity = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)
    storage_location = Column(String(150))
    condition = Column(String(50), default="Good")
    item_image = Column(String(255))
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    supplier = relationship("Supplier")


class AssignItem(Base):
    __tablename__ = "assign_items"
    id = Column(Integer, primary_key=True, index=True)
    assign_number = Column(String(50), unique=True, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    assign_type = Column(String(30), nullable=False)  # Department/Classroom/Teacher
    reference_id = Column(Integer)
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    assigned_date = Column(DateTime, default=_now)
    status = Column(String(20), default="Pending")  # Pending/Assigned/Completed
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    item = relationship("InventoryItem")
    assigned_user = relationship("User")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    order_date = Column(DateTime, default=_now)
    expected_delivery_date = Column(DateTime)
    status = Column(String(30), default="Draft")  # Draft/Sent/Approved/Partially Received/Received
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    supplier = relationship("Supplier")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    item = relationship("InventoryItem")


class Receiving(Base):
    __tablename__ = "receiving"
    id = Column(Integer, primary_key=True, index=True)
    receiving_number = Column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"))
    purchase_order_item_id = Column(Integer, ForeignKey("purchase_order_items.id"))
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity_received = Column(Integer, nullable=False)
    receiver_name = Column(String(150))
    date_received = Column(DateTime, default=_now)
    status = Column(String(20), default="Pending")  # Pending/Received
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    item = relationship("InventoryItem")


class ReturnRecord(Base):
    __tablename__ = "returns"
    id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity_returned = Column(Integer, nullable=False)
    return_reason = Column(Text)
    condition = Column(String(20), default="Good")  # Good/Damaged
    date_returned = Column(DateTime, default=_now)
    received_by = Column(String(150))
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    item = relationship("InventoryItem")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)  # IN/OUT/ADJUSTMENT
    source_type = Column(String(30))  # Assignment/Receiving/Return/Manual
    source_id = Column(Integer)
    quantity = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    notes = Column(Text)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=_now)

    item = relationship("InventoryItem")


class SystemSettings(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    system_name = Column(String(150), default="School Stock Management System")
    school_name = Column(String(150), default="Demo School")
    system_logo = Column(String(255))
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50))
    module = Column(String(50))
    record_id = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime, default=_now)

    user = relationship("User")
