import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import RoleGuard from './components/RoleGuard.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Inventory from './pages/Inventory.jsx'
import Assignments from './pages/Assignments.jsx'
import Departments from './pages/Departments.jsx'
import Suppliers from './pages/Suppliers.jsx'
import PurchaseOrders from './pages/PurchaseOrders.jsx'
import Receiving from './pages/Receiving.jsx'
import Returns from './pages/Returns.jsx'
import Reports from './pages/Reports.jsx'
import StockMovements from './pages/StockMovements.jsx'
import Users from './pages/Users.jsx'
import Profile from './pages/Profile.jsx'
import Settings from './pages/Settings.jsx'
import AuditLogs from './pages/AuditLogs.jsx'
import AccessDenied from './components/AccessDenied.jsx'
import { LanguageProvider } from './context/LanguageContext.jsx'

export default function App() {
  return (
    <LanguageProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<RoleGuard permission="view_inventory"><Inventory /></RoleGuard>} />
          <Route path="/assignments" element={<RoleGuard permission="view_assignments"><Assignments /></RoleGuard>} />
          <Route path="/departments" element={<RoleGuard permission="view_departments"><Departments /></RoleGuard>} />
          <Route path="/suppliers" element={<RoleGuard permission="view_suppliers"><Suppliers /></RoleGuard>} />
          <Route path="/purchase-orders" element={<RoleGuard permission="manage_po"><PurchaseOrders /></RoleGuard>} />
          <Route path="/receiving" element={<RoleGuard permission="manage_receiving"><Receiving /></RoleGuard>} />
          <Route path="/returns" element={<RoleGuard permission="manage_returns"><Returns /></RoleGuard>} />
          <Route path="/reports" element={<RoleGuard permission="view_reports"><Reports /></RoleGuard>} />
          <Route path="/stock-movements" element={<RoleGuard permission="view_movements"><StockMovements /></RoleGuard>} />
          <Route path="/users" element={<RoleGuard permission="manage_users"><Users /></RoleGuard>} />
          <Route path="/audit-logs" element={<RoleGuard permission="view_audit"><AuditLogs /></RoleGuard>} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<RoleGuard permission="manage_settings"><Settings /></RoleGuard>} />
          <Route path="/access-denied" element={<AccessDenied />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Route>
      </Routes>
    </LanguageProvider>
  )
}