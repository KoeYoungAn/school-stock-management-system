# Global Form Validation Implementation Guide
## School Stock Management System

Generated: 2026-06-12

---

## Summary of Changes

This document provides exact code changes needed to implement global form validation across all forms in the system.

### Files to Create
1. ✅ `frontend/src/utils/validation.js` - **DONE**
2. ✅ `frontend/src/hooks/useValidation.js` - **DONE**

### Files to Modify (Frontend)
1. ✅ `frontend/src/components/FormInput.jsx` - **DONE**
2. ✅ `frontend/src/components/SelectInput.jsx` - **DONE**
3. `frontend/src/pages/Users.jsx` - Add validation schema & hook
4. `frontend/src/pages/Inventory.jsx` - Add validation schema & hook
5. `frontend/src/pages/Suppliers.jsx` (uses _MasterDataPage.jsx) - Add validation to MasterDataPage
6. `frontend/src/pages/Departments.jsx` (uses _MasterDataPage.jsx) - Add validation to MasterDataPage
7. `frontend/src/pages/Assignments.jsx` - Add validation schema & hook
8. `frontend/src/pages/PurchaseOrders.jsx` - Add validation schema & hook
9. `frontend/src/pages/Receiving.jsx` - Add validation schema & hook
10. `frontend/src/pages/Returns.jsx` - Add validation schema & hook
11. `frontend/src/pages/Profile.jsx` - Add validation schema & hook
12. `frontend/src/pages/Settings.jsx` - Add validation schema & hook
13. `frontend/src/pages/_MasterDataPage.jsx` - Add validation schema & hook

### Files to Modify (Backend)
1. `backend/schemas.py` - Add Pydantic validators for required fields
2. `backend/main.py` - Add RequestValidationError exception handler

---

## Frontend Changes Required

### Pattern for Each Page

Each page needs:

1. **Import validation utilities**
```javascript
import { useValidation } from '../hooks/useValidation.js'
import { required, email, minLength, selectRequired, positiveNumber } from '../utils/validation.js'
```

2. **Define validation schema(s)**
```javascript
const formSchema = {
  field_name: [required('Field Name'), minLength(2, 'Field Name')],
  email_field: [required('Email'), email('Email')],
  quantity: [required('Quantity'), positiveNumber('Quantity')],
  select_field: [selectRequired('Select Field')]
}
```

3. **Initialize hook in component**
```javascript
const { errors, validateAll, handleBlur } = useValidation(formSchema)
```

4. **Add validation to submit handler**
```javascript
const submit = async (e) => {
  e.preventDefault()
  
  // Validate before API call
  const { isValid, errors: validationErrors } = validateAll(form)
  if (!isValid) {
    toast.error('Please fix validation errors')
    return
  }
  
  // Proceed with API call
  try {
    // ... existing API call code
  } catch(e) {
    toast.error(errMsg(e))
  }
}
```

5. **Update form fields with error prop**
```javascript
<FormInput
  label={t('fieldName', language)}
  required
  error={errors.field_name}
  onBlur={(e) => handleBlur('field_name', e.target.value)}
  value={form.field_name}
  onChange={e => setForm({...form, field_name: e.target.value})}
/>
```

6. **Disable submit button when invalid**
```javascript
<button
  disabled={Object.values(errors).some(e => e)}
  className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
>
  {t('save', language)}
</button>
```

---

## Specific Schema Definitions by Page

### Users.jsx

```javascript
const userCreateSchema = {
  full_name: [required('Full Name'), minLength(2, 'Full Name')],
  email: [required('Email'), email('Email')],
  password: [required('Password'), minLength(6, 'Password')]
}

const userEditSchema = {
  full_name: [required('Full Name'), minLength(2, 'Full Name')],
  email: [required('Email'), email('Email')]
}

const passwordResetSchema = {
  new_password: [required('New Password'), minLength(6, 'New Password')]
}

// Use in component:
const schema = edit ? userEditSchema : userCreateSchema
const { errors, validateAll, handleBlur } = useValidation(schema)

// In password reset modal:
const pwSchema = passwordResetSchema
const { errors: pwErrors, validateAll: validatePw } = useValidation(pwSchema)
```

### Inventory.jsx

```javascript
const inventorySchema = {
  item_name: [required('Item Name'), minLength(2, 'Item Name')],
  minimum_stock: [minLength(0, 'Minimum Stock') || required('Minimum Stock')]
}
```

### Suppliers.jsx (via _MasterDataPage.jsx)

```javascript
const supplierSchema = {
  supplier_name: [required('Supplier Name'), minLength(2, 'Supplier Name')]
}
```

### Departments.jsx (via _MasterDataPage.jsx)

```javascript
const departmentSchema = {
  department_name: [required('Department Name'), minLength(2, 'Department Name')]
}
```

### Assignments.jsx

```javascript
const assignmentSchema = {
  item_id: [selectRequired('Item')],
  quantity: [required('Quantity'), positiveNumber('Quantity')]
}
```

### PurchaseOrders.jsx

```javascript
const poSchema = {
  supplier_id: [selectRequired('Supplier')] // CRITICAL: was missing!
}

// Note: For line items, validate in addLine/setLine functions:
const validateLineItems = (items) => {
  return items.length > 0 && items.every(l => l.item_id && l.quantity_ordered > 0)
}
```

### Receiving.jsx

```javascript
const receivingSchema = {
  item_id: [selectRequired('Item')],
  quantity_received: [required('Quantity'), positiveNumber('Quantity')]
}
```

### Returns.jsx

```javascript
const returnSchema = {
  item_id: [selectRequired('Item')],
  quantity_returned: [required('Quantity'), positiveNumber('Quantity')]
}
```

### Profile.jsx

```javascript
const profileSchema = {
  full_name: [required('Full Name'), minLength(2, 'Full Name')]
}

const passwordSchema = {
  current_password: [required('Current Password')],
  new_password: [required('New Password'), minLength(6, 'New Password')]
}
```

### Settings.jsx

```javascript
const settingsSchema = {
  system_name: [required('System Name'), minLength(2, 'System Name')],
  school_name: [required('School Name'), minLength(2, 'School Name')]
}
```

### _MasterDataPage.jsx

```javascript
// Accept validationSchema prop
export default function MasterDataPage({
  base, title, fields, blankForm, columns,
  editPerm='manage_inventory', deletePerm='delete_critical',
  nameKey, validationSchema = {} // NEW
})

// Build schema from fields marked required:true
const requiredFields = fields.filter(f => f.required)
const autoSchema = requiredFields.reduce((acc, f) => {
  acc[f.name] = [required(f.labelKey || f.label)]
  return acc
}, {})

// Merge with passed schema
const finalSchema = { ...autoSchema, ...validationSchema }

const { errors, validateAll, handleBlur } = useValidation(finalSchema)
```

---

## Backend Changes Required

### backend/schemas.py

Add validators to reject empty strings:

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

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

# Apply similar validators to:
class SupplierCreate(SupplierBase):
    @field_validator('supplier_name')
    @classmethod
    def supplier_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Supplier name is required')
        return v.strip()

class DepartmentCreate(DepartmentBase):
    @field_validator('department_name')
    @classmethod
    def dept_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Department name is required')
        return v.strip()

class InventoryCreate(InventoryBase):
    @field_validator('item_name')
    @classmethod
    def item_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Item name is required')
        return v.strip()

class POCreate(POBase):
    items: List[POItemCreate] = Field(min_items=1)  # At least 1 item required!
    
    @field_validator('supplier_id')
    @classmethod
    def supplier_required(cls, v):
        if not v:
            raise ValueError('Supplier is required')
        return v
```

### backend/main.py

Add exception handler:

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field = '.'.join(str(loc) for loc in error['loc'] if loc != 'body')
        errors.append({
            'field': field,
            'message': error['msg']
        })
    return JSONResponse(
        status_code=422,
        content={
            'detail': 'Validation failed',
            'errors': errors
        }
    )
```

---

## Implementation Priority

1. **High Priority (Core Forms)**
   - Users.jsx
   - Inventory.jsx
   - PurchaseOrders.jsx
   - Settings.jsx

2. **Medium Priority**
   - Suppliers.jsx
   - Departments.jsx
   - Assignments.jsx
   - Receiving.jsx
   - Returns.jsx

3. **Lower Priority**
   - Profile.jsx
   - _MasterDataPage.jsx

---

## Testing Checklist

- [ ] Try submitting Users form with empty fields → See red borders & error messages
- [ ] Try submitting Inventory with whitespace-only item_name → Rejected
- [ ] Try submitting PurchaseOrders without supplier → Rejected
- [ ] Try submitting Assignments without quantity → Rejected
- [ ] Try submitting with negative quantities → Rejected
- [ ] Try invalid email in Suppliers → See error
- [ ] Verify submit button disabled when form invalid
- [ ] Verify backend returns 422 with proper error format
- [ ] Verify errors cleared on successful submit

---

## Notes

- All validation happens on blur AND on submit
- Required fields show red asterisk (*)
- Invalid fields show red border
- Error messages appear below field
- Submit button is disabled while form has errors
- Backend validators ensure data integrity even if frontend bypassed
- Empty strings and whitespace-only values are rejected everywhere
