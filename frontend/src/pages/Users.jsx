import React, { useEffect, useState } from 'react'
import api from '../api/api.js'
import DataTable from '../components/DataTable.jsx'
import Pagination from '../components/Pagination.jsx'
import Modal from '../components/Modal.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import FormInput from '../components/FormInput.jsx'
import SelectInput from '../components/SelectInput.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import { useToast } from '../components/Toast.jsx'
import { errMsg } from '../utils/helpers.js'
import { ROLES, STATUSES } from '../utils/constants.js'
import { Plus, Pencil, Trash2, KeyRound } from 'lucide-react'
import { useValidation } from '../hooks/useValidation.js'
import { required, email, minLength } from '../utils/validation.js'

const blank = { full_name:'', email:'', phone:'', role:'Teacher', status:'Active', password:'' }

const userCreateSchema = {
  full_name: [required('Full Name'), minLength(2, 'Full Name')],
  email: [required('Email'), email('Email')],
  password: [required('Password'), minLength(6, 'Password')]
}

const userEditSchema = {
  full_name: [required('Full Name'), minLength(2, 'Full Name')],
  email: [required('Email'), email('Email')]
}

const passwordResetSchema = {
  new_password: [required('New Password'), minLength(6, 'New Password')]
}

export default function Users() {
  const { user: me } = useAuth(); const toast = useToast()
  const { language } = useLanguage()
  const [rows,setRows]=useState([]); const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1); const [limit,setLimit]=useState(20)
  const [search,setSearch]=useState(''); const [role,setRole]=useState(''); const [status,setStatus]=useState('')
  const [loading,setLoading]=useState(false)
  const [open,setOpen]=useState(false); const [edit,setEdit]=useState(null)
  const [form,setForm]=useState(blank); const [del,setDel]=useState(null)
  const [pwUser,setPwUser]=useState(null); const [newPw,setNewPw]=useState('')
  const { errors, validateAll, handleBlur, clearErrors, hasErrors } = useValidation(edit ? userEditSchema : userCreateSchema)
  const { errors: pwErrors, validateAll: validatePw, handleBlur: handlePwBlur, clearErrors: clearPwErrors, hasErrors: hasPwErrors } = useValidation(passwordResetSchema)
  const load=async()=>{
    setLoading(true)
    try{const r=await api.get('/api/users',{params:{page,limit,search,role,status}});setRows(r.data.items);setTotal(r.data.total)}
    catch(e){toast.error(errMsg(e))}finally{setLoading(false)}
  }
  useEffect(()=>{load()},[page,limit,role,status])
  const openNew=()=>{setEdit(null);setForm(blank);clearErrors();setOpen(true)}
  const openEdit=(r)=>{setEdit(r);setForm({...blank,...r,password:''});clearErrors();setOpen(true)}
  const openPasswordReset=(r)=>{setPwUser(r);setNewPw('');clearPwErrors()}
  const submit=async(e)=>{
    e.preventDefault()
    const { isValid } = validateAll(form)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try{
      if(edit){
        const {password,...rest}=form
        await api.put(`/api/users/${edit.id}`,rest)
      } else {
        await api.post('/api/users',form)
      }
      toast.success('Saved');setOpen(false);load()
    }catch(e){toast.error(errMsg(e))}
  }
  const remove=async()=>{try{await api.delete(`/api/users/${del.id}`);toast.success('Deleted');setDel(null);load()}catch(e){toast.error(errMsg(e))}}
  const resetPw=async()=>{
    const { isValid } = validatePw({ new_password: newPw })
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try{await api.post(`/api/users/${pwUser.id}/reset-password`,{new_password:newPw});toast.success('Password reset');setPwUser(null);setNewPw('')}
    catch(e){toast.error(errMsg(e))}
  }
  const columns = [
    { key:'full_name', label:t('name', language) },
    { key:'email', label:t('email', language) },
    { key:'phone', label:t('phone', language) },
    { key:'role', label:t('role', language), render:r=> <StatusBadge value={r.role}/> },
    { key:'status', label:t('status', language), render:r=> <StatusBadge value={r.status}/> },
    { key:'_a', label:t('actions', language), render:r=>(
      <div className="flex gap-2">
        <button onClick={()=>openEdit(r)} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700" title={t('edit', language)}><Pencil className="w-4 h-4"/></button>
        <button onClick={()=>openPasswordReset(r)} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700" title={t('changePassword', language)}><KeyRound className="w-4 h-4"/></button>
        {r.id !== me.id && <button onClick={()=>setDel(r)} className="p-1 text-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900/30" title={t('delete', language)}><Trash2 className="w-4 h-4"/></button>}
      </div>
    )},
  ]
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <input value={search} onChange={e=>setSearch(e.target.value)} onKeyDown={e=>e.key==='Enter'&&(setPage(1),load())}
          placeholder={t('search', language)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
        <select value={role} onChange={e=>{setRole(e.target.value);setPage(1)}}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
          <option value="">{t('role', language)}</option>{ROLES.map(r=> <option key={r}>{r}</option>)}
        </select>
        <select value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
          <option value="">{t('allStatus', language)}</option>{STATUSES.map(s=> <option key={s}>{s}</option>)}
        </select>
        <div className="ml-auto"/>
        <button onClick={openNew} className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"><Plus className="w-4 h-4"/> {t('newUser', language)}</button>
      </div>
      <DataTable columns={columns} rows={rows} loading={loading} emptyTitle={t('noUsers', language)}/>
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit}/>

      <Modal open={open} onClose={()=>setOpen(false)} title={edit ? t('editUser', language) : t('newUser', language)} size="md">
        <form onSubmit={submit} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormInput label={t('fullName', language)} required value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}
            error={errors.full_name} onBlur={e=>handleBlur('full_name', e.target.value)}/>
          <FormInput label={t('email', language)} type="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})}
            error={errors.email} onBlur={e=>handleBlur('email', e.target.value)}/>
          <FormInput label={t('phone', language)} value={form.phone||''} onChange={e=>setForm({...form,phone:e.target.value})}/>
          <SelectInput label={t('role', language)} value={form.role} onChange={e=>setForm({...form,role:e.target.value})} options={ROLES}/>
          <SelectInput label={t('status', language)} value={form.status} onChange={e=>setForm({...form,status:e.target.value})} options={STATUSES}/>
          {!edit && <FormInput label={t('password', language)} type="password" required minLength="6" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}
            error={errors.password} onBlur={e=>handleBlur('password', e.target.value)}/>}
          <div className="sm:col-span-2 flex justify-end gap-2 pt-2">
            <button type="button" onClick={()=>setOpen(false)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
            <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
          </div>
        </form>
      </Modal>

      <Modal open={!!pwUser} onClose={()=>setPwUser(null)} title={`${t('changePassword', language)}: ${pwUser?.email}`} size="sm">
        <div className="space-y-3">
          <FormInput label={t('newPassword', language)} type="password" minLength="6" required value={newPw} onChange={e=>setNewPw(e.target.value)}
            error={pwErrors.new_password} onBlur={e=>handlePwBlur('new_password', e.target.value)}/>
          <div className="flex justify-end gap-2">
            <button onClick={()=>setPwUser(null)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
            <button onClick={resetPw} disabled={hasPwErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog open={!!del} onClose={()=>setDel(null)} onConfirm={remove} message={`${t('deleteUser', language)} ${del?.email}?`}/>
    </div>
  )
}
