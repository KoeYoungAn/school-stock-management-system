import React, { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import Navbar from './Navbar.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'

const TITLE_KEYS = {
  '/': 'dashboard', '/inventory': 'inventory', '/assignments': 'assignItems',
  '/departments': 'departments', '/suppliers': 'suppliers',
  '/purchase-orders': 'purchaseOrders', '/receiving': 'receiving',
  '/returns': 'returns', '/reports': 'reports', '/stock-movements': 'stockMovements',
  '/users': 'users', '/audit-logs': 'auditLogs', '/profile': 'profile', '/settings': 'settings',
}

export default function Layout() {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  const { language } = useLanguage()
  const titleKey = TITLE_KEYS[loc.pathname] || 'dashboard'
  const title = t(titleKey, language)
  return (
    <div className="flex h-screen">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar title={title} onToggleSidebar={() => setOpen(o => !o)} />
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
