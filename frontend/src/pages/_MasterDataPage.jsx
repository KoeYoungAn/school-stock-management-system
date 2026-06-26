// Generic master-data CRUD page builder for Departments and Suppliers
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
import { can } from '../utils/permissions.js'
import { errMsg } from '../utils/helpers.js'
import { Plus, Pencil, Trash2, Eye } from 'lucide-react'
import { useValidation } from '../hooks/useValidation.js'
import { required } from '../utils/validation.js'

export default function MasterDataPage({
  base, title, fields, blankForm, columns,
  editPerm='manage_inventory', deletePerm='delete_critical',
  nameKey,
  validationSchema = {},
}) {
  const { user } = useAuth(); const toast = useToast()
  const { language } = useLanguage()
  const pageTitle = title.key ? t(title.key, language) : title
  const newTitle = title.newKey ? t(title.newKey, language) : `${t('add', language)} ${pageTitle}`
  const editTitle = title.editKey ? t(title.editKey, language) : `${t('edit', language)} ${pageTitle}`
  const emptyTitle = title.emptyKey ? t(title.emptyKey, language) : `No ${pageTitle} records`
  const [rows,setRows]=useState([]); const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1); const [limit,setLimit]=useState(20)
  const [search,setSearch]=useState(''); const [loading,setLoading]=useState(false)
  const [open,setOpen]=useState(false); const [edit,setEdit]=useState(null)
  const [form,setForm]=useState(blankForm); const [del,setDel]=useState(null)
  const [viewDetail, setViewDetail] = useState(null)

  // Build schema from required fields + passed-in schema
  const requiredFields = fields.filter(f => f.required)
  const autoSchema = requiredFields.reduce((acc, f) => {
    acc[f.name] = [required(f.labelKey ? t(f.labelKey, language) : f.label)]
    return acc
  }, {})
  const finalSchema = { ...autoSchema, ...validationSchema }
  const { errors, validateAll, handleBlur, clearErrors, hasErrors } = useValidation(finalSchema)

  const load = async () => {
    setLoading(true)
    try { const r=await api.get(base,{params:{page,limit,search}}); setRows(r.data.items); setTotal(r.data.total) }
    catch(e){toast.error(errMsg(e))} finally{setLoading(false)}
  }
  useEffect(()=>{load()},[page,limit])
  const openNew=()=>{setEdit(null);setForm(blankForm);clearErrors();setOpen(true)}
  const openEdit=(r)=>{setEdit(r);setForm({...blankForm,...r});clearErrors();setOpen(true)}
  const submit=async(e)=>{
    e.preventDefault()
    const { isValid } = validateAll(form)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try{
      if(edit) await api.put(`${base}/${edit.id}`,form)
      else await api.post(base,form)
      toast.success('Saved'); setOpen(false); load()
    }catch(e){toast.error(errMsg(e))}
  }
  const remove=async()=>{
    try{await api.delete(`${base}/${del.id}`); toast.success('Deleted'); setDel(null); load()}
    catch(e){toast.error(errMsg(e))}
  }
  const canEdit = can(user, editPerm)
  const canDelete = can(user, deletePerm)
  const tableCols = [
    ...columns.map(c => ({ ...c, label: c.labelKey ? t(c.labelKey, language) : c.label })),
    { key:'status', label:t('status', language), render:r => <StatusBadge value={r.status}/> },
    { key:'_a', label:t('actions', language), render:r=>(
      <div className="flex gap-2">
        <button onClick={()=>setViewDetail(r)} className="p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 text-blue-600" title={t('viewDetails', language)}>
          <Eye className="w-5 h-5" />
        </button>
        {canEdit && <button onClick={()=>openEdit(r)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title={t('edit', language)}>
          <Pencil className="w-5 h-5" />
        </button>}
        {canDelete && <button onClick={()=>setDel(r)} className="p-2 text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30" title={t('delete', language)}>
          <Trash2 className="w-5 h-5" />
        </button>}
      </div>
    )},
  ]
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <input value={search} onChange={e=>setSearch(e.target.value)} onKeyDown={e=>e.key==='Enter'&&(setPage(1),load())}
          placeholder={t('search', language)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
        <button onClick={()=>{setPage(1);load()}} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('search', language)}</button>
        <div className="ml-auto"/>
        {canEdit && <button onClick={openNew} className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"><Plus className="w-4 h-4"/> {newTitle}</button>}
      </div>
      <DataTable columns={tableCols} rows={rows} loading={loading} emptyTitle={emptyTitle}/>
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit}/>
      <Modal open={open} onClose={()=>setOpen(false)} title={edit ? editTitle : newTitle} size="md">
        <form onSubmit={submit} className="grid grid-cols-1 gap-3">
          {fields.map(f =>
            f.type==='select'
              ? <SelectInput key={f.name} label={f.labelKey ? t(f.labelKey, language) : f.label} value={form[f.name]||''} onChange={e=>setForm({...form,[f.name]:e.target.value})} options={f.options}
                  error={errors[f.name]} onBlur={e=>handleBlur(f.name, e.target.value)} required={f.required}/>
              : f.type==='textarea'
              ? <label key={f.name} className="block">
                  <span className="block text-sm font-medium mb-1">{f.labelKey ? t(f.labelKey, language) : f.label}</span>
                  <textarea value={form[f.name]||''} onChange={e=>setForm({...form,[f.name]:e.target.value})} rows="2"
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
                </label>
              : <FormInput key={f.name} label={f.labelKey ? t(f.labelKey, language) : f.label} required={f.required} type={f.type||'text'}
                  value={form[f.name]||''} onChange={e=>setForm({...form,[f.name]:e.target.value})}
                  error={errors[f.name]} onBlur={e=>handleBlur(f.name, e.target.value)}/>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={()=>setOpen(false)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
            <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
          </div>
        </form>
      </Modal>
      <ConfirmDialog open={!!del} onClose={()=>setDel(null)} onConfirm={remove}
        message={`Delete "${del?.[nameKey]}"?`}/>

      <Modal open={!!viewDetail} onClose={()=>setViewDetail(null)} title={`${pageTitle} ${t('viewDetails', language)}`} size="lg">
        {viewDetail && (
          <div className="space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-2xl font-semibold mb-2">{viewDetail[nameKey]}</h3>
                <StatusBadge value={viewDetail.status} />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {fields.filter(f => f.type !== 'textarea').map(field => (
                <div key={field.name}>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    {field.labelKey ? t(field.labelKey, language) : field.label}
                  </label>
                  <div className="text-base font-medium">
                    {field.type === 'select' && field.name === 'status'
                      ? <StatusBadge value={viewDetail[field.name]} />
                      : viewDetail[field.name] || '—'
                    }
                  </div>
                </div>
              ))}
            </div>

            {fields.filter(f => f.type === 'textarea').map(field => (
              viewDetail[field.name] && (
                <div key={field.name}>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                    {field.labelKey ? t(field.labelKey, language) : field.label}
                  </label>
                  <div className="text-base p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                    {viewDetail[field.name]}
                  </div>
                </div>
              )
            ))}

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              {canEdit && (
                <button onClick={()=>{setViewDetail(null); openEdit(viewDetail)}}
                  className="px-5 py-3 text-base rounded-lg bg-blue-600 text-white hover:bg-blue-700">
                  {editTitle}
                </button>
              )}
              <button onClick={()=>setViewDetail(null)}
                className="px-5 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800">
                {t('close', language)}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
