import React, { useEffect, useState } from 'react'
import { Moon, Sun, Menu } from 'lucide-react'
import { useTheme } from '../context/ThemeContext.jsx'
import { useSettings } from '../context/SettingsContext.jsx'
import UserDropdown from './UserDropdown.jsx'
import LanguageSwitcher from './LanguageSwitcher.jsx'

export default function Navbar({ title, onToggleSidebar }) {
  const { dark, toggle } = useTheme()
  const { settings } = useSettings()
  const sysName = settings?.system_name || 'School Stock'
  return (
    <header className="h-20 flex items-center justify-between px-6 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-4">
        <button onClick={onToggleSidebar} className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
          <Menu className="w-6 h-6" />
        </button>
        <div>
          <div className="text-sm text-gray-500 dark:text-gray-400">{sysName}</div>
          <h1 className="font-semibold text-xl leading-tight">{title}</h1>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <LanguageSwitcher />
        <button onClick={toggle} className="p-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                title="Toggle dark mode">
          {dark ? <Sun className="w-6 h-6" /> : <Moon className="w-6 h-6" />}
        </button>
        <UserDropdown />
      </div>
    </header>
  )
}
