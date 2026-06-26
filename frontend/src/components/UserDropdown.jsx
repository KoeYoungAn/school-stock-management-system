import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { UPLOAD_BASE } from '../api/api.js'
import { initials } from '../utils/helpers.js'
import { can } from '../utils/permissions.js'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import StatusBadge from './StatusBadge.jsx'
import { LogOut, User, Settings as SettingsIcon } from 'lucide-react'

export default function UserDropdown() {
  const { user, logout } = useAuth()
  const { language } = useLanguage()
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const ref = useRef(null)
  useEffect(() => {
    const h = (e) => { if (!ref.current?.contains(e.target)) setOpen(false) }
    document.addEventListener('click', h); return () => document.removeEventListener('click', h)
  }, [])
  if (!user) return null
  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(!open)}
        className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
        {user.profile_photo
          ? <img src={`${UPLOAD_BASE}/${user.profile_photo}`} alt="" className="w-10 h-10 rounded-full object-cover"/>
          : <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center text-base font-semibold">
              {initials(user.full_name)}
            </div>}
        <span className="hidden sm:block text-base">{user.full_name}</span>
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-30">
          <div className="p-4 border-b border-gray-100 dark:border-gray-700">
            <div className="font-medium text-base">{user.full_name}</div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{user.email}</div>
            <div className="mt-2"><StatusBadge value={user.role} /></div>
          </div>
          <Link to="/profile" onClick={()=>setOpen(false)} className="flex items-center gap-3 px-4 py-3 text-base hover:bg-gray-50 dark:hover:bg-gray-700">
            <User className="w-5 h-5" /> {t('profile', language)}
          </Link>
          {can(user, 'manage_settings') && (
            <Link to="/settings" onClick={()=>setOpen(false)} className="flex items-center gap-3 px-4 py-3 text-base hover:bg-gray-50 dark:hover:bg-gray-700">
              <SettingsIcon className="w-5 h-5" /> {t('settings', language)}
            </Link>
          )}
          <button onClick={async()=>{ await logout(); navigate('/login') }}
            className="w-full text-left flex items-center gap-3 px-4 py-3 text-base text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-b-xl">
            <LogOut className="w-5 h-5" /> {t('logout', language)}
          </button>
        </div>
      )}
    </div>
  )
}
