import React, { createContext, useContext, useEffect, useState } from 'react'
import api from '../api/api.js'

const AuthCtx = createContext(null)
export const useAuth = () => useContext(AuthCtx)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    try {
      const r = await api.get('/api/auth/me')
      setUser(r.data.user)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  const login = async (email, password) => {
    const r = await api.post('/api/auth/login', { email, password })
    setUser(r.data.user)
    return r.data.user
  }

  const logout = async () => {
    try { await api.post('/api/auth/logout') } catch {}
    setUser(null)
  }

  return (
    <AuthCtx.Provider value={{ user, loading, login, logout, refresh, setUser }}>
      {children}
    </AuthCtx.Provider>
  )
}
