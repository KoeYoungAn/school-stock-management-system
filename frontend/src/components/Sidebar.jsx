import React, { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useSettings } from '../context/SettingsContext.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import { can } from '../utils/permissions.js'
import { UPLOAD_BASE } from '../api/api.js'
import {
  LayoutDashboard, Boxes, ClipboardList, Building2, Truck,
  ShoppingCart, PackageCheck, Undo2, FileBarChart2, Activity,
  Users, ScrollText, UserCircle, Settings,
} from 'lucide-react'

const ALL = [
  { to:'/', labelKey:'dashboard', icon: LayoutDashboard, perm:'view_dashboard' },
  { to:'/inventory', labelKey:'inventory', icon: Boxes, perm:'view_inventory' },
  { to:'/assignments', labelKey:'assignItems', icon: ClipboardList, perm:'view_assignments' },
  { to:'/departments', labelKey:'departments', icon: Building2, perm:'view_departments' },
  { to:'/suppliers', labelKey:'suppliers', icon: Truck, perm:'view_suppliers' },
  { to:'/purchase-orders', labelKey:'purchaseOrders', icon: ShoppingCart, perm:'manage_po' },
  { to:'/receiving', labelKey:'receiving', icon: PackageCheck, perm:'manage_receiving' },
  { to:'/returns', labelKey:'returns', icon: Undo2, perm:'manage_returns' },
  { to:'/reports', labelKey:'reports', icon: FileBarChart2, perm:'view_reports' },
  { to:'/stock-movements', labelKey:'stockMovements', icon: Activity, perm:'view_movements' },
  { to:'/users', labelKey:'users', icon: Users, perm:'manage_users' },
  { to:'/audit-logs', labelKey:'auditLogs', icon: ScrollText, perm:'view_audit' },
  { to:'/profile', labelKey:'profile', icon: UserCircle, perm:'edit_profile' },
  { to:'/settings', labelKey:'settings', icon: Settings, perm:'manage_settings' },
]

export default function Sidebar({ open, onClose }) {
  const { user } = useAuth()
  const { settings } = useSettings()
  const { language } = useLanguage()
  const items = ALL.filter(i => can(user, i.perm))

  return (
    <>
      {open && <div onClick={onClose} className="fixed inset-0 bg-black/40 z-20 md:hidden" />}
      <aside className={`fixed md:static z-30 inset-y-0 left-0 w-72 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform ${open?'translate-x-0':'-translate-x-full'} md:translate-x-0 transition-transform`}>
        <div className="h-20 flex items-center gap-4 px-6 border-b border-gray-200 dark:border-gray-700">
          {settings?.system_logo
            ? <img src={`${UPLOAD_BASE}/${settings.system_logo}`} alt="logo" className="w-12 h-12 rounded object-cover" />
            : <div className="w-12 h-12 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xl">S</div>}
          <div className="font-semibold text-lg truncate">{settings?.school_name || 'School'}</div>
        </div>
        <nav className="p-3 space-y-1 overflow-y-auto h-[calc(100vh-5rem)]">
          {items.map(it => (
            <NavLink key={it.to} to={it.to} end={it.to==='/'} onClick={onClose}
              className={({isActive}) => `flex items-center gap-4 px-4 py-3 rounded-lg text-base ${isActive?'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium':'hover:bg-gray-100 dark:hover:bg-gray-700'}`}>
              <it.icon className="w-5 h-5" />
              <span>{t(it.labelKey, language)}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}
