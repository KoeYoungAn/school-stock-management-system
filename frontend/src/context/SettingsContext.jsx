import React, { createContext, useContext, useEffect, useState } from 'react'
import api from '../api/api.js'

const SettingsCtx = createContext(null)
export const useSettings = () => useContext(SettingsCtx)

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    try {
      const r = await api.get('/api/settings')
      setSettings(r.data)
    } catch {
      setSettings(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  return (
    <SettingsCtx.Provider value={{ settings, loading, refresh }}>
      {children}
    </SettingsCtx.Provider>
  )
}
