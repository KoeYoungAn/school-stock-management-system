import React, { createContext, useCallback, useContext, useState } from 'react'
const Ctx = createContext(null)
export const useToast = () => useContext(Ctx)

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const push = useCallback((msg, type='info') => {
    const id = Date.now() + Math.random()
    setItems(p => [...p, { id, msg, type }])
    setTimeout(() => setItems(p => p.filter(t => t.id !== id)), 4000)
  }, [])
  const ctx = {
    success: (m) => push(m, 'success'),
    error: (m) => push(m, 'error'),
    info: (m) => push(m, 'info'),
  }
  return (
    <Ctx.Provider value={ctx}>
      {children}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {items.map(t => (
          <div key={t.id} className={`px-4 py-2 rounded-lg shadow-lg text-sm text-white ${
            t.type==='success' ? 'bg-green-600' : t.type==='error' ? 'bg-red-600' : 'bg-gray-700'
          }`}>{t.msg}</div>
        ))}
      </div>
    </Ctx.Provider>
  )
}
