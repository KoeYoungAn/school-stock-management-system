import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import { useTheme } from '../context/ThemeContext.jsx'
import { useToast } from '../components/Toast.jsx'
import api, { UPLOAD_BASE } from '../api/api.js'
import { Moon, Sun, LogIn } from 'lucide-react'
import { errMsg } from '../utils/helpers.js'

export default function Login() {
  const { user, login } = useAuth()
  const { dark, toggle } = useTheme()
  const { language, setLanguage } = useLanguage()
  const toast = useToast()
  const nav = useNavigate()
  const [email, setEmail] = useState('admin@school.local')
  const [password, setPassword] = useState('admin123')
  const [busy, setBusy] = useState(false)
  const [settings, setSettings] = useState(null)

  useEffect(() => {
    api.get('/api/settings').then(r => setSettings(r.data)).catch(()=>{})
  }, [])
  useEffect(() => { if (user) nav('/') }, [user])

  const submit = async (e) => {
    e.preventDefault(); setBusy(true)
    try { await login(email, password); nav('/') }
    catch (err) { toast.error(errMsg(err)) }
    finally { setBusy(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <button onClick={toggle} className="absolute top-6 right-6 p-3 rounded-lg bg-white dark:bg-gray-800 shadow-lg">
        {dark ? <Sun className="w-6 h-6"/> : <Moon className="w-6 h-6"/>}
      </button>
      <button onClick={() => setLanguage(language === 'en' ? 'kh' : 'en')} className="absolute top-6 right-20 px-4 py-3 rounded-lg bg-white dark:bg-gray-800 shadow-lg font-medium">
        {language === 'en' ? 'ភាសាខ្មែរ' : 'English'}
      </button>
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg p-10">
        <div className="text-center mb-8">
          {settings?.system_logo
            ? <img src={`${UPLOAD_BASE}/${settings.system_logo}`} alt="" className="w-20 h-20 mx-auto rounded-xl object-cover" />
            : <div className="w-20 h-20 mx-auto rounded-xl bg-blue-600 text-white text-3xl font-bold flex items-center justify-center">S</div>}
          <h1 className="mt-4 text-2xl font-semibold">{settings?.system_name || 'School Stock Management System'}</h1>
          <p className="text-base text-gray-500 dark:text-gray-400 mt-1">{settings?.school_name || 'Demo School'}</p>
        </div>
        <form onSubmit={submit} className="space-y-5">
          <label className="block">
            <span className="block text-base font-medium mb-2">{t('email', language)}</span>
            <input value={email} onChange={e=>setEmail(e.target.value)} required type="email"
              className="w-full px-4 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-blue-500" />
          </label>
          <label className="block">
            <span className="block text-base font-medium mb-2">{t('password', language)}</span>
            <input value={password} onChange={e=>setPassword(e.target.value)} required type="password" minLength={6}
              className="w-full px-4 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-blue-500" />
          </label>
          <button disabled={busy} type="submit"
            className="w-full inline-flex items-center justify-center gap-2 py-3 text-base font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60">
            <LogIn className="w-5 h-5"/> {busy ? '...' : t('loginButton', language)}
          </button>
        </form>
        <div className="mt-6 text-sm text-gray-500 dark:text-gray-400 space-y-2 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <div className="font-medium mb-2">Demo Accounts:</div>
          <div><b>Admin:</b> admin@school.local / admin123</div>
          <div><b>Storekeeper:</b> storekeeper@school.local / store123</div>
          <div><b>Teacher:</b> teacher@school.local / teacher123</div>
        </div>
      </div>
    </div>
  )
}
