# School Stock Management System
session id  93df4120-1bd4-4fdb-9097-5edebed68010
A complete school inventory & stock management system with FastAPI backend and React (Vite) frontend.

## Folder Structure
```
school-stock-management-system/
  backend/            # FastAPI + SQLite + SQLAlchemy
  frontend/           # React + Vite + Tailwind CDN + Axios
  README.md
```

## Backend Setup
```
cd backend
pip install fastapi uvicorn sqlalchemy pydantic python-multipart reportlab
python -m uvicorn main:app --reload
```
Runs at `http://localhost:8000`. Database `school_stock.db` is auto-created and seeded on first run.

## Frontend Setup
```
cd frontend
npm install
npm run dev
```
Runs at `http://localhost:5173`. The API base URL is `http://localhost:8000` by default; override with `VITE_API_BASE` env var.

## Default Logins
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@school.local | admin123 |
| Storekeeper | storekeeper@school.local | store123 |
| Teacher | teacher@school.local | teacher123 |

## Authentication
HttpOnly signed-cookie session. Login via `POST /api/auth/login`, current user from `GET /api/auth/me`. The frontend uses Axios with `withCredentials: true`. **No localStorage / sessionStorage is used** — refreshing the page re-validates the session via `/api/auth/me`.

## Permissions
Backend enforces all permissions via FastAPI dependencies (`require_admin`, `require_staff`):
- **Admin** — full access (users, settings, audit logs, PO approval, deletes, reports export).
- **Storekeeper** — inventory, assignments, receiving, returns, Draft/Sent POs, view suppliers/departments/reports/movements.
- **Teacher** — dashboard, inventory (read-only), own profile, own assigned items only.

Frontend hides controls based on permissions (`src/utils/permissions.js`) but the backend is the source of truth — it returns `401` if not logged in and `403` if forbidden.

## File Uploads
Files (item images, profile photos, system logo) are uploaded as multipart form data using `python-multipart` and stored under `backend/uploads/`. The DB stores only the relative filename. Files are served via `GET /uploads/...` (FastAPI StaticFiles). Allowed types: jpg, jpeg, png, webp. Max size: 5MB.

## Stock Logic
Every stock change writes a row in `stock_movements`:
- **Assignment** with status `Assigned` or `Completed` → OUT movement.
- **Receiving** with status `Received` → IN movement and updates `purchase_order_item.quantity_received`; PO status auto-transitions Draft → Sent → Partially Received → Received.
- **Returns** — Good condition → IN movement; Damaged → audit note only (no stock increase).
- Editing/deleting any of the above first reverses then re-applies stock effects so the ledger stays correct.
- Stock is prevented from going negative.

## Purchase Orders
POs support multiple line items (`PurchaseOrderItem`). `total_items` is computed from line items. Receiving links to PO line items and updates received quantities. Only Admins can approve or delete a PO.

## Reports & PDF Export
- `/api/reports/stock-summary` returns totals + filtered rows.
- `/api/reports/low-stock` returns items below minimum.
- `/api/reports/stock-movements` returns recent ledger entries.
- `/api/reports/export-pdf?report=stock-summary|low-stock|movements` returns a PDF generated server-side with `reportlab`. Includes the system name, school name, and uploaded logo (gracefully falls back to text branding).

## Dark / Light Mode
Tailwind class-based dark mode controlled by React Context (`ThemeContext`). It does **not** persist after refresh (per project rules). Toggle from the navbar.

## API Base URL
Edit `frontend/src/api/api.js` or set `VITE_API_BASE` to point the frontend at a different backend.

## Health Check
`GET /api/health` returns API + database status.
