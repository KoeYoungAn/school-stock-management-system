import React, { useState, useRef, useEffect } from 'react'
import { useLanguage } from '../context/LanguageContext.jsx'
import { Globe } from 'lucide-react'

export default function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!ref.current?.contains(event.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        title="Switch Language / ជ្រើសរើសភាសា"
      >
        <Globe className="w-5 h-5 text-gray-600 dark:text-gray-300" />
        <span className="text-base font-medium text-gray-700 dark:text-gray-200">
          {language === 'kh' ? 'ភាសា' : 'Language'}
        </span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-30 overflow-hidden">
          <button
            onClick={() => { setLanguage('en'); setOpen(false) }}
            className={`w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
              language === 'en' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-300' : ''
            }`}
          >
            <span className="text-xl">🇺🇸</span>
            <div>
              <div className="font-medium">English</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">English</div>
            </div>
            {language === 'en' && (
              <span className="ml-auto text-blue-600 dark:text-blue-300">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </span>
            )}
          </button>

          <button
            onClick={() => { setLanguage('kh'); setOpen(false) }}
            className={`w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
              language === 'kh' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-300' : ''
            }`}
          >
            <span className="text-xl">🇰🇭</span>
            <div>
              <div className="font-medium">ភាសាខ្មែរ</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Khmer</div>
            </div>
            {language === 'kh' && (
              <span className="ml-auto text-blue-600 dark:text-blue-300">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </span>
            )}
          </button>
        </div>
      )}
    </div>
  )
}