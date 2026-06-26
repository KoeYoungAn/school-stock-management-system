import React, { useEffect, useState } from 'react'
import api, { UPLOAD_BASE } from '../api/api.js'
import FormInput from '../components/FormInput.jsx'
import FileUploadInput from '../components/FileUploadInput.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import { useToast } from '../components/Toast.jsx'
import { errMsg } from '../utils/helpers.js'
import { useValidation } from '../hooks/useValidation.js'
import { required, minLength } from '../utils/validation.js'

const profileSchema = {
  full_name: [required('Full Name'), minLength(2, 'Full Name')]
}

const passwordSchema = {
  current_password: [required('Current Password')],
  new_password: [required('New Password'), minLength(6, 'New Password')]
}

export default function Profile() {
  const { user, refresh } = useAuth(); const toast = useToast()
  const { language } = useLanguage()
  const [form,setForm]=useState({full_name:'',phone:''}); const [photo,setPhoto]=useState(null)
  const [pw,setPw]=useState({current_password:'',new_password:''})
  const { errors, validateAll, handleBlur, hasErrors } = useValidation(profileSchema)
  const { errors: pwErrors, validateAll: validatePw, handleBlur: handlePwBlur, hasErrors: hasPwErrors } = useValidation(passwordSchema)
  useEffect(()=>{ if(user) setForm({full_name:user.full_name,phone:user.phone||''}) },[user])
  const save = async (e) => {
    e.preventDefault()
    const { isValid } = validateAll(form)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try {
      const fd = new FormData(); fd.append('full_name',form.full_name); fd.append('phone',form.phone)
      if (photo) fd.append('photo',photo)
      await api.put('/api/profile',fd); toast.success(t('profileUpdated', language)); refresh()
    } catch(e){toast.error(errMsg(e))}
  }
  const changePw = async (e) => {
    e.preventDefault()
    const { isValid } = validatePw(pw)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try { await api.post('/api/auth/change-password',pw); toast.success(t('passwordChanged', language)); setPw({current_password:'',new_password:''}) }
    catch(e){toast.error(errMsg(e))}
  }
  if (!user) return null
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-5">
        <h3 className="font-semibold mb-4">{t('myProfile', language)}</h3>
        <div className="flex items-center gap-3 mb-4">
          {user.profile_photo
            ? <img src={`${UPLOAD_BASE}/${user.profile_photo}`} alt="" className="w-16 h-16 rounded-full object-cover"/>
            : <div className="w-16 h-16 rounded-full bg-blue-600 text-white flex items-center justify-center text-xl font-bold">{user.full_name?.[0]}</div>}
          <div>
            <div className="font-medium">{user.full_name}</div>
            <div className="text-sm text-gray-500">{user.email}</div>
            <StatusBadge value={user.role}/>
          </div>
        </div>
        <form onSubmit={save} className="space-y-3">
          <FormInput label={t('fullName', language)} required value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}
            error={errors.full_name} onBlur={e=>handleBlur('full_name', e.target.value)}/>
          <FormInput label={t('phone', language)} value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})}/>
          <FileUploadInput label={t('systemLogo', language)} onChange={setPhoto} preview={user.profile_photo?`${UPLOAD_BASE}/${user.profile_photo}`:null}/>
          <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
        </form>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-5">
        <h3 className="font-semibold mb-4">{t('changePassword', language)}</h3>
        <form onSubmit={changePw} className="space-y-3">
          <FormInput label={t('currentPassword', language)} type="password" required value={pw.current_password} onChange={e=>setPw({...pw,current_password:e.target.value})}
            error={pwErrors.current_password} onBlur={e=>handlePwBlur('current_password', e.target.value)}/>
          <FormInput label={t('newPassword', language)} type="password" required minLength="6" value={pw.new_password} onChange={e=>setPw({...pw,new_password:e.target.value})}
            error={pwErrors.new_password} onBlur={e=>handlePwBlur('new_password', e.target.value)}/>
          <button disabled={hasPwErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('changePassword', language)}</button>
        </form>
      </div>
    </div>
  )
}
