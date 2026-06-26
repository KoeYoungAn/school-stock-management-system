// Frontend permission helpers (UI hint only — backend enforces real permissions).
export const ROLES = { ADMIN: 'Admin', STOREKEEPER: 'Storekeeper', TEACHER: 'Teacher' }

export const can = (user, action) => {
  if (!user) return false
  const role = user.role
  const map = {
    'manage_users': ['Admin'],
    'view_audit': ['Admin'],
    'manage_settings': ['Admin'],
    'approve_po': ['Admin'],
    'delete_critical': ['Admin'],
    'export_reports': ['Admin'],
    'manage_inventory': ['Admin', 'Storekeeper'],
    'manage_assignments': ['Admin', 'Storekeeper'],
    'manage_receiving': ['Admin', 'Storekeeper'],
    'manage_returns': ['Admin', 'Storekeeper'],
    'manage_po': ['Admin', 'Storekeeper'],
    'view_suppliers': ['Admin', 'Storekeeper'],
    'view_departments': ['Admin', 'Storekeeper'],
    'view_reports': ['Admin', 'Storekeeper'],
    'view_movements': ['Admin', 'Storekeeper'],
    'view_inventory': ['Admin', 'Storekeeper', 'Teacher'],
    'view_assignments': ['Admin', 'Storekeeper', 'Teacher'],
    'view_dashboard': ['Admin', 'Storekeeper', 'Teacher'],
    'edit_profile': ['Admin', 'Storekeeper', 'Teacher'],
  }
  return (map[action] || []).includes(role)
}
