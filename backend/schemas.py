from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, field_validator
import re


# ---------- Auth ----------
class LoginIn(BaseModel):
    email: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


# ---------- User ----------
class UserBase(BaseModel):
    full_name: str = Field(min_length=1)
    email: str
    phone: Optional[str] = None
    role: str = "Teacher"
    status: str = "Active"

    @field_validator('full_name', 'email')
    @classmethod
    def not_empty_or_whitespace(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace only')
        return v.strip()

    @field_validator('email')
    @classmethod
    def valid_email_format(cls, v):
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class UserCreate(UserBase):
    password: str = Field(min_length=6)

    @field_validator('password')
    @classmethod
    def password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserOut(UserBase):
    id: int
    profile_photo: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResetPasswordIn(BaseModel):
    new_password: str = Field(min_length=6)


# ---------- Supplier ----------
class SupplierBase(BaseModel):
    supplier_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "Active"
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    @field_validator('supplier_name')
    @classmethod
    def supplier_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Supplier name is required')
        return v.strip()


class SupplierUpdate(SupplierBase):
    supplier_name: Optional[str] = None
    status: Optional[str] = None


class SupplierOut(SupplierBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Department ----------
class DepartmentBase(BaseModel):
    department_name: str
    department_head: Optional[str] = None
    room_code: Optional[str] = None
    location: Optional[str] = None
    status: str = "Active"
    notes: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    @field_validator('department_name')
    @classmethod
    def dept_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Department name is required')
        return v.strip()


class DepartmentUpdate(DepartmentBase):
    department_name: Optional[str] = None
    status: Optional[str] = None


class DepartmentOut(DepartmentBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Inventory ----------
class InventoryBase(BaseModel):
    item_name: str
    category: Optional[str] = None
    unit: Optional[str] = "pcs"
    supplier_id: Optional[int] = None
    stock_quantity: int = 0
    minimum_stock: int = 0
    storage_location: Optional[str] = None
    condition: Optional[str] = "Good"
    notes: Optional[str] = None


class InventoryCreate(InventoryBase):
    @field_validator('item_name')
    @classmethod
    def item_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Item name is required')
        return v.strip()


class InventoryUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    supplier_id: Optional[int] = None
    stock_quantity: Optional[int] = None
    minimum_stock: Optional[int] = None
    storage_location: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None


class InventoryOut(InventoryBase):
    id: int
    item_code: str
    item_image: Optional[str] = None
    stock_status: Optional[str] = None
    supplier_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Assignment ----------
class AssignBase(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)
    assign_type: str
    reference_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    status: str = "Pending"
    notes: Optional[str] = None


class AssignCreate(AssignBase):
    pass


class AssignUpdate(BaseModel):
    item_id: Optional[int] = None
    quantity: Optional[int] = None
    assign_type: Optional[str] = None
    reference_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AssignOut(AssignBase):
    id: int
    assign_number: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    assigned_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Purchase Order ----------
class POItemBase(BaseModel):
    item_id: int
    quantity_ordered: int = Field(gt=0)
    notes: Optional[str] = None


class POItemCreate(POItemBase):
    pass


class POItemUpdate(BaseModel):
    item_id: Optional[int] = None
    quantity_ordered: Optional[int] = None
    notes: Optional[str] = None


class POItemOut(POItemBase):
    id: int
    purchase_order_id: int
    quantity_received: int
    item_name: Optional[str] = None
    item_code: Optional[str] = None

    class Config:
        from_attributes = True


class POBase(BaseModel):
    supplier_id: int
    expected_delivery_date: Optional[datetime] = None
    status: str = "Draft"
    notes: Optional[str] = None


class POCreate(POBase):
    items: List[POItemCreate] = []


class POUpdate(BaseModel):
    supplier_id: Optional[int] = None
    expected_delivery_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class POOut(POBase):
    id: int
    po_number: str
    order_date: Optional[datetime] = None
    supplier_name: Optional[str] = None
    total_items: Optional[int] = 0
    items: List[POItemOut] = []

    class Config:
        from_attributes = True


# ---------- Receiving ----------
class ReceivingBase(BaseModel):
    purchase_order_id: Optional[int] = None
    purchase_order_item_id: Optional[int] = None
    item_id: int
    quantity_received: int = Field(gt=0)
    receiver_name: Optional[str] = None
    status: str = "Pending"
    notes: Optional[str] = None


class ReceivingCreate(ReceivingBase):
    pass


class ReceivingUpdate(BaseModel):
    quantity_received: Optional[int] = None
    receiver_name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ReceiveMoreRequest(BaseModel):
    additional_quantity: int = Field(gt=0)
    receiver_name: str
    status: str = "Received"
    notes: Optional[str] = None


class DirectReceiptCreate(BaseModel):
    """Direct stock receipt without PO - for opening stock, donations, emergency receipt"""
    item_id: int
    quantity: int = Field(gt=0)
    source: str = Field(min_length=1)  # e.g., "Opening Stock", "Donation", "Emergency"
    reason: str = Field(min_length=1)  # e.g., "Initial inventory", "Donated by..."
    receiver_name: str = Field(min_length=1)
    notes: Optional[str] = None


class ReceivingOut(ReceivingBase):
    id: int
    receiving_number: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    date_received: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Returns ----------
class ReturnBase(BaseModel):
    item_id: int
    quantity_returned: int = Field(gt=0)
    return_reason: Optional[str] = None
    condition: str = "Good"
    received_by: Optional[str] = None
    notes: Optional[str] = None


class ReturnCreate(ReturnBase):
    pass


class ReturnUpdate(BaseModel):
    quantity_returned: Optional[int] = None
    return_reason: Optional[str] = None
    condition: Optional[str] = None
    received_by: Optional[str] = None
    notes: Optional[str] = None


class ReturnOut(ReturnBase):
    id: int
    return_number: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    date_returned: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Stock Movement ----------
class MovementOut(BaseModel):
    id: int
    item_id: int
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    movement_type: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    quantity: int
    balance_after: int
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Settings ----------
class SettingsOut(BaseModel):
    id: int
    system_name: str
    school_name: str
    system_logo: Optional[str] = None

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    system_name: Optional[str] = None
    school_name: Optional[str] = None


# ---------- Audit log ----------
class AuditOut(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str] = None
    action: Optional[str]
    module: Optional[str]
    record_id: Optional[int]
    description: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class ListResp(BaseModel):
    items: List[Any]
    total: int
    page: int
    limit: int
