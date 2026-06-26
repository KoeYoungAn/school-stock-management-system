import React, { useEffect, useState } from 'react'
import api, { UPLOAD_BASE } from '../api/api.js'
import FormInput from '../components/FormInput.jsx'
import FileUploadInput from '../components/FileUploadInput.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { useSettings } from '../context/SettingsContext.jsx'
import { t } from '../utils/translations.js'
import { useToast } from '../components/Toast.jsx'
import { errMsg } from '../utils/helpers.js'
import { useValidation } from '../hooks/useValidation.js'
import { required, minLength } from '../utils/validation.js'

const settingsSchema = {
  system_name: [required('System Name'), minLength(2, 'System Name')],
  school_name: [required('School Name'), minLength(2, 'School Name')]
}

export default function Settings() {
  const toast = useToast()
  const { language } = useLanguage()
  const { refresh: refreshSettings } = useSettings()
  const [s,setS]=useState({system_name:'',school_name:'',system_logo:null})
  const [orig,setOrig]=useState(null); const [logo,setLogo]=useState(null); const [preview,setPreview]=useState(null)
  const { errors, validateAll, handleBlur, hasErrors } = useValidation(settingsSchema)
  const load = async () => {
    try { const r=await api.get('/api/settings'); setS(r.data); setOrig(r.data) }
    catch(e){toast.error(errMsg(e))}
  }
  useEffect(()=>{load()},[])
  useEffect(()=>{
    if (logo) { const u=URL.createObjectURL(logo); setPreview(u); return ()=>URL.revokeObjectURL(u) }
    setPreview(null)
  },[logo])
  const save = async (e) => {
    e.preventDefault()
    const { isValid } = validateAll(s)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try {
      const fd = new FormData()
      fd.append('system_name',s.system_name); fd.append('school_name',s.school_name)
      if (logo) fd.append('logo',logo)
      await api.put('/api/settings',fd); toast.success(t('settingsUpdated', language)); setLogo(null); load(); refreshSettings()
    } catch(e){toast.error(errMsg(e))}
  }
  return (
    <div className="max-w-2xl bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-5">
      <h3 className="font-semibold mb-4">{t('systemSettings', language)}</h3>
      <form onSubmit={save} className="space-y-4">
        <FormInput label={t('systemName', language)} required value={s.system_name||''} onChange={e=>setS({...s,system_name:e.target.value})}
          error={errors.system_name} onBlur={e=>handleBlur('system_name', e.target.value)}/>
        <FormInput label={t('schoolName', language)} required value={s.school_name||''} onChange={e=>setS({...s,school_name:e.target.value})}
          error={errors.school_name} onBlur={e=>handleBlur('school_name', e.target.value)}/>
        <div>
          <FileUploadInput label={t('systemLogo', language)} onChange={setLogo}
            preview={preview || (s.system_logo?`${UPLOAD_BASE}/${s.system_logo}`:null)}/>
          <p className="text-xs text-gray-500 mt-1">JPG, PNG, WEBP — max 5MB.</p>
        </div>
        <div className="flex gap-2">
          <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('saveSettings', language)}</button>
          <button type="button" onClick={()=>{setS(orig);setLogo(null)}} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
        </div>
      </form>
    </div>
  )
}
