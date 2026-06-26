import React, { createContext, useContext, useState, useEffect } from 'react'

const LanguageContext = createContext(null)

export const useLanguage = () => useContext(LanguageContext)

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    // Try to get language from localStorage
    const saved = localStorage.getItem('school-inventory-language')
    if (saved === 'kh' || saved === 'en') {
      return saved
    }
    // Default to English
    return 'en'
  })

  // Set direction based on language (RTL for Arabic, etc.)
  useEffect(() => {
    // For Khmer, we might need special handling, but for now just set dir
    if (language === 'kh') {
      document.documentElement.setAttribute('lang', 'km')
      document.documentElement.setAttribute('dir', 'ltr') // Khmer is LTR
    } else {
      document.documentElement.setAttribute('lang', 'en')
      document.documentElement.setAttribute('dir', 'ltr')
    }

    // Save to localStorage
    localStorage.setItem('school-inventory-language', language)
  }, [language])

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'en' ? 'kh' : 'en')
  }

  const setLanguageExplicit = (lang) => {
    if (lang === 'en' || lang === 'kh') {
      setLanguage(lang)
    }
  }

  return (
    <LanguageContext.Provider value={{
      language,
      toggleLanguage,
      setLanguage: setLanguageExplicit,
      isKhmer: language === 'kh',
      isEnglish: language === 'en'
    }}>
      {children}
    </LanguageContext.Provider>
  )
}

// Import translations
import { t as getTranslation } from '../utils/translations.js'

// Translation utilities
export const t = (key, context) => {
  const lang = context?.language || 'en'
  return getTranslation(key, lang)
}