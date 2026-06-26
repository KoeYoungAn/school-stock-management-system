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
import { errMsg, fmtDate } from '../utils/helpers.js'
import { ASSIGN_TYPES, ASSIGN_STATUSES } from '../utils/constants.js'
import { Plus, Pencil, Trash2, Eye } from 'lucide-react'
import { useValidation } from '../hooks/useValidation.js'
import { required, selectRequired, positiveNumber } from '../utils/validation.js'

const assignmentSchema = {
  item_id: [selectRequired('Item')],
  quantity: [required('Quantity'), positiveNumber('Quantity')]
}

const blank = { item_id:'', quantity:1, assign_type:'Department', reference_id:'', assigned_user_id:'', status:'Pending', notes:'' }

export default function Assignments() {
  const { user } = useAuth(); const toast = useToast()
  const { language } = useLanguage()
  const [rows,setRows]=useState([]); const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1); const [limit,setLimit]=useState(20)
  const [search,setSearch]=useState(''); const [status,setStatus]=useState('')
  const [loading,setLoading]=useState(false)
  const [open,setOpen]=useState(false); const [edit,setEdit]=useState(null)
  const [form,setForm]=useState(blank); const [del,setDel]=useState(null)
  const [viewDetail, setViewDetail] = useState(null)
  const [items,setItems]=useState([]); const [users,setUsers]=useState([]); const [deps,setDeps]=useState([])
  const { errors, validateAll, handleBlur, clearErrors, hasErrors } = useValidation(assignmentSchema)

  const load = async () => {
    setLoading(true)
    try {
      const r = await api.get('/api/assignments', { params: { page, limit, search, status } })
      setRows(r.data.items); setTotal(r.data.total)
    } catch(e){toast.error(errMsg(e))} finally { setLoading(false) }
  }
  useEffect(()=>{load()},[page,limit,status])
  useEffect(()=>{
    api.get('/api/inventory?limit=500').then(r=>setItems(r.data.items)).catch(()=>{})
    api.get('/api/departments?limit=500').then(r=>setDeps(r.data.items)).catch(()=>{})
    if (can(user,'manage_users')) api.get('/api/users?limit=500').then(r=>setUsers(r.data.items)).catch(()=>{})
  },[])

  const openNew = () => { setEdit(null); setForm({ ...blank, assign_type: 'Department' }); clearErrors(); setOpen(true) }
  const openEdit = (r) => { setEdit(r); setForm({...r, reference_id:r.reference_id||'', assigned_user_id:r.assigned_user_id||''}); clearErrors(); setOpen(true) }
  const submit = async (e) => {
    e.preventDefault()
    const { isValid } = validateAll(form)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try {
      const payload = {...form, item_id:Number(form.item_id), quantity:Number(form.quantity)}
      if (payload.reference_id==='') payload.reference_id=null; else payload.reference_id=Number(payload.reference_id)
      if (payload.assigned_user_id==='') payload.assigned_user_id=null; else payload.assigned_user_id=Number(payload.assigned_user_id)
      if (edit) await api.put(`/api/assignments/${edit.id}`, payload)
      else await api.post('/api/assignments', payload)
      toast.success('Saved'); setOpen(false); load()
    } catch(e){toast.error(errMsg(e))}
  }
  const remove = async () => {
    try { await api.delete(`/api/assignments/${del.id}`); toast.success('Deleted'); setDel(null); load() }
    catch(e){toast.error(errMsg(e))}
  }
  const canEdit = can(user,'manage_assignments')
  const canDelete = can(user,'delete_critical')
  const columns = [
    { key:'assign_number', label:t('number', language) },
    { key:'item_name', label:t('item', language), render:r=>`${r.item_code||''} ${r.item_name||''}` },
    { key:'quantity', label:t('qty', language) },
    { key:'assign_type', label:t('type', language) },
    { key:'status', label:t('status', language), render:r=> <StatusBadge value={r.status}/> },
    { key:'assigned_date', label:t('date', language), render:r=>fmtDate(r.assigned_date) },
    { key:'_a', label:t('actions', language), render:r=>(
      <div className="flex gap-2">
        <button onClick={()=>setViewDetail(r)} className="p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 text-blue-600" title={t('viewDetails', language)}>
          <Eye className="w-5 h-5" />
        </button>
        {canEdit && <button onClick={()=>openEdit(r)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title={t('edit', language)}>
          <Pencil className="w-5 h-5" />
        </button>}
        {canDelete && <button onClick={()=>setDel(r)} className="p-2 rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30" title={t('delete', language)}>
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
        <select value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
          <option value="">All status</option>
          {ASSIGN_STATUSES.map(s=> <option key={s}>{s}</option>)}
        </select>
        <div className="ml-auto"/>
        {canEdit && <button onClick={openNew} className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"><Plus className="w-4 h-4"/> {t('newAssignment', language)}</button>}
      </div>
      <DataTable columns={columns} rows={rows} loading={loading} emptyTitle={t('noAssignments', language)}/>
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit}/>
      <Modal open={open} onClose={()=>setOpen(false)} title={edit ? t('editAssignment', language) : t('newAssignment', language)} size="lg">
        <form onSubmit={submit} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <SelectInput label={t('item', language)} required value={form.item_id} onChange={e=>setForm({...form,item_id:e.target.value})}
            options={[{value:'',label:'— Select —'}, ...items.map(i=>({value:i.id,label:`${i.item_code} ${i.item_name} (stock ${i.stock_quantity})`}))]}
            error={errors.item_id} onBlur={e=>handleBlur('item_id', e.target.value)}/>
          <FormInput type="number" min="1" label={t('quantity', language)} required value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})}
            error={errors.quantity} onBlur={e=>handleBlur('quantity', e.target.value)}/>
          <SelectInput label={t('type', language)} value={form.assign_type} onChange={e=>setForm({...form,assign_type:e.target.value})} options={ASSIGN_TYPES}/>
          {form.assign_type==='Department' && (
            <SelectInput label={t('department', language)} value={form.reference_id} onChange={e=>setForm({...form,reference_id:e.target.value})}
              options={[{value:'',label:'— None —'}, ...deps.map(d=>({value:d.id,label:d.department_name}))]}/>
          )}
          <SelectInput label={t('assignedUser', language)} value={form.assigned_user_id} onChange={e=>setForm({...form,assigned_user_id:e.target.value})}
            options={[{value:'',label:'— None —'}, ...users.map(u=>({value:u.id,label:`${u.full_name} (${u.role})`}))]}/>
          <SelectInput label={t('status', language)} value={form.status} onChange={e=>setForm({...form,status:e.target.value})} options={ASSIGN_STATUSES}/>
          <label className="sm:col-span-2 block">
            <span className="block text-sm font-medium mb-1">{t('notes', language)}</span>
            <textarea value={form.notes||''} onChange={e=>setForm({...form,notes:e.target.value})} rows="2"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
          </label>
          <div className="sm:col-span-2 flex justify-end gap-2">
            <button type="button" onClick={()=>setOpen(false)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
            <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
          </div>
        </form>
      </Modal>
      <ConfirmDialog open={!!del} onClose={()=>setDel(null)} onConfirm={remove} message={`${t('deleteAssignment', language)} ${del?.assign_number}?`}/>

      <Modal open={!!viewDetail} onClose={()=>setViewDetail(null)} title={t('assignmentDetails', language)} size="lg">
        {viewDetail && (
          <div className="space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-2xl font-semibold mb-2">{viewDetail.assign_number}</h3>
                <div className="flex items-center gap-3">
                  <StatusBadge value={viewDetail.status} />
                  <span className="text-sm text-gray-500 dark:text-gray-400">{fmtDate(viewDetail.assigned_date)}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('item', language)}</label>
                <div className="text-base font-medium">{viewDetail.item_code} - {viewDetail.item_name}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('quantity', language)}</label>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{viewDetail.quantity}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('assignmentType', language)}</label>
                <div className="text-base font-medium">{viewDetail.assign_type}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('assignmentDate', language)}</label>
                <div className="text-base font-medium">{fmtDate(viewDetail.assigned_date)}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('status', language)}</label>
                <StatusBadge value={viewDetail.status} />
              </div>
            </div>

            {viewDetail.notes && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{t('notes', language)}</label>
                <div className="text-base p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                  {viewDetail.notes}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              {canEdit && (
                <button onClick={()=>{setViewDetail(null); openEdit(viewDetail)}}
                  className="px-5 py-3 text-base rounded-lg bg-blue-600 text-white hover:bg-blue-700">
                  {t('editAssignment', language)}
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
