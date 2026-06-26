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
import { PO_STATUSES } from '../utils/constants.js'
import { Plus, Pencil, Trash2, Eye, Check } from 'lucide-react'
import { useValidation } from '../hooks/useValidation.js'
import { selectRequired } from '../utils/validation.js'

const poSchema = {
  supplier_id: [selectRequired('Supplier')]
}

export default function PurchaseOrders() {
  const { user } = useAuth(); const toast = useToast()
  const { language } = useLanguage()
  const [rows,setRows]=useState([]); const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1); const [limit,setLimit]=useState(20)
  const [status,setStatus]=useState(''); const [loading,setLoading]=useState(false)
  const [open,setOpen]=useState(false); const [edit,setEdit]=useState(null)
  const [view,setView]=useState(null); const [del,setDel]=useState(null)
  const [suppliers,setSuppliers]=useState([]); const [items,setItems]=useState([])
  const [form,setForm]=useState({ supplier_id:'', expected_delivery_date:'', status:'Draft', notes:'', items:[] })
  const { errors, validateAll, handleBlur, clearErrors, hasErrors } = useValidation(poSchema)

  const load = async () => {
    setLoading(true)
    try { const r=await api.get('/api/purchase-orders',{params:{page,limit,status}}); setRows(r.data.items); setTotal(r.data.total) }
    catch(e){toast.error(errMsg(e))} finally{setLoading(false)}
  }
  useEffect(()=>{load()},[page,limit,status])
  useEffect(()=>{
    api.get('/api/suppliers?limit=500').then(r=>setSuppliers(r.data.items)).catch(()=>{})
    api.get('/api/inventory?limit=500').then(r=>setItems(r.data.items)).catch(()=>{})
  },[])

  const openNew = () => { setEdit(null); setForm({ supplier_id:'', expected_delivery_date:'', status:'Draft', notes:'', items:[{item_id:'',quantity_ordered:1}] }); clearErrors(); setOpen(true) }
  const openEdit = (r) => { setEdit(r); setForm({
    supplier_id:r.supplier_id, expected_delivery_date: r.expected_delivery_date?.slice(0,10)||'', status:r.status, notes:r.notes||'',
    items: r.items
  }); clearErrors(); setOpen(true) }

  const addLine = () => setForm(f => ({...f, items:[...f.items, {item_id:'',quantity_ordered:1}]}))
  const setLine = (i, patch) => setForm(f => ({...f, items: f.items.map((x,ix)=> ix===i?{...x,...patch}:x)}))
  const rmLine = (i) => setForm(f => ({...f, items: f.items.filter((_,ix)=>ix!==i)}))

  const submit = async (e) => {
    e.preventDefault()
    const { isValid } = validateAll(form)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    if (form.items.length === 0 || !form.items.every(l => l.item_id && l.quantity_ordered > 0)) {
      toast.error('Please add at least one valid line item'); return
    }
    try {
      const payload = {
        supplier_id: Number(form.supplier_id),
        expected_delivery_date: form.expected_delivery_date ? new Date(form.expected_delivery_date).toISOString() : null,
        status: form.status, notes: form.notes,
      }
      if (edit) {
        await api.put(`/api/purchase-orders/${edit.id}`, payload)
      } else {
        payload.items = form.items.filter(l=>l.item_id).map(l=>({item_id:Number(l.item_id), quantity_ordered:Number(l.quantity_ordered), notes:l.notes||null}))
        await api.post('/api/purchase-orders', payload)
      }
      toast.success('Saved'); setOpen(false); load()
    } catch(e){toast.error(errMsg(e))}
  }
  const remove = async () => {
    try{await api.delete(`/api/purchase-orders/${del.id}`); toast.success('Deleted'); setDel(null); load()}
    catch(e){toast.error(errMsg(e))}
  }
  const approve = async (id) => {
    try{await api.put(`/api/purchase-orders/${id}/approve`); toast.success('Approved'); load()} catch(e){toast.error(errMsg(e))}
  }
  const canEdit = can(user,'manage_po')
  const canApprove = can(user,'approve_po')
  const canDelete = can(user,'delete_critical')
  const columns = [
    { key:'po_number', label:t('poNumber', language) },
    { key:'supplier_name', label:t('supplier', language) },
    { key:'order_date', label:t('orderDate', language), render:r=>fmtDate(r.order_date) },
    { key:'expected_delivery_date', label:t('expectedDate', language), render:r=>fmtDate(r.expected_delivery_date) },
    { key:'total_items', label:'Lines' },
    { key:'status', label:t('status', language), render:r=> <StatusBadge value={r.status}/> },
    { key:'_a', label:t('actions', language), render:r=>(
      <div className="flex gap-2">
        <button onClick={()=>setView(r)} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700" title={t('viewDetails', language)}><Eye className="w-4 h-4"/></button>
        {canEdit && <button onClick={()=>openEdit(r)} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700" title={t('edit', language)}><Pencil className="w-4 h-4"/></button>}
        {canApprove && r.status!=='Approved' && r.status!=='Received' &&
          <button onClick={()=>approve(r.id)} className="p-1 text-emerald-600 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/30" title="Approve"><Check className="w-4 h-4"/></button>}
        {canDelete && <button onClick={()=>setDel(r)} className="p-1 text-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900/30" title={t('delete', language)}><Trash2 className="w-4 h-4"/></button>}
      </div>
    )},
  ]
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <select value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
          <option value="">{t('allStatus', language)}</option>
          {PO_STATUSES.map(s=> <option key={s}>{s}</option>)}
        </select>
        <div className="ml-auto"/>
        {canEdit && <button onClick={openNew} className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"><Plus className="w-4 h-4"/> {t('newPurchaseOrder', language)}</button>}
      </div>
      <DataTable columns={columns} rows={rows} loading={loading} emptyTitle={t('noPurchaseOrders', language)}/>
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit}/>

      <Modal open={open} onClose={()=>setOpen(false)} title={edit ? t('editPurchaseOrder', language) : t('newPurchaseOrder', language)} size="lg">
        <form onSubmit={submit} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <SelectInput label={t('supplier', language)} value={form.supplier_id} onChange={e=>setForm({...form,supplier_id:e.target.value})}
              options={[{value:'',label:'— Select —'}, ...suppliers.map(s=>({value:s.id,label:s.supplier_name}))]}
              error={errors.supplier_id} onBlur={e=>handleBlur('supplier_id', e.target.value)} required />
            <FormInput type="date" label={t('expectedDate', language)} value={form.expected_delivery_date} onChange={e=>setForm({...form,expected_delivery_date:e.target.value})}/>
            <SelectInput label={t('status', language)} value={form.status} onChange={e=>setForm({...form,status:e.target.value})}
              options={user.role==='Storekeeper' ? ['Draft','Sent'] : PO_STATUSES}/>
          </div>
          {!edit && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-sm">Line Items</h4>
                <button type="button" onClick={addLine} className="px-2 py-1 text-sm rounded border border-gray-300 dark:border-gray-600">+ {t('addItem', language)}</button>
              </div>
              {form.items.map((l,i)=>(
                <div key={i} className="grid grid-cols-12 gap-2 mb-2">
                  <select value={l.item_id} onChange={e=>setLine(i,{item_id:e.target.value})}
                    className="col-span-7 px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
                    <option value="">— Item —</option>
                    {items.map(it=> <option key={it.id} value={it.id}>{it.item_code} {it.item_name}</option>)}
                  </select>
                  <input type="number" min="1" value={l.quantity_ordered} onChange={e=>setLine(i,{quantity_ordered:e.target.value})}
                    className="col-span-3 px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
                  <button type="button" onClick={()=>rmLine(i)} className="col-span-2 px-2 py-1 rounded border border-red-300 text-red-600">{t('removeItem', language)}</button>
                </div>
              ))}
            </div>
          )}
          <label className="block">
            <span className="block text-sm font-medium mb-1">{t('notes', language)}</span>
            <textarea value={form.notes||''} onChange={e=>setForm({...form,notes:e.target.value})} rows="2"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
          </label>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={()=>setOpen(false)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
            <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
          </div>
        </form>
      </Modal>

      <Modal open={!!view} onClose={()=>setView(null)} title={`${t('poDetails', language)} ${view?.po_number}`} size="lg">
        {view && (
          <div className="space-y-3 text-sm">
            <div><b>{t('supplier', language)}:</b> {view.supplier_name}</div>
            <div><b>{t('status', language)}:</b> <StatusBadge value={view.status}/></div>
            <div><b>{t('orderDate', language)}:</b> {fmtDate(view.order_date)} · <b>{t('expectedDate', language)}:</b> {fmtDate(view.expected_delivery_date)}</div>
            <table className="min-w-full border border-gray-200 dark:border-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800"><tr>
                <th className="text-left px-2 py-1">{t('item', language)}</th><th className="px-2 py-1">Ordered</th><th className="px-2 py-1">Received</th>
              </tr></thead>
              <tbody>
                {view.items.map(i=>(
                  <tr key={i.id} className="border-t border-gray-100 dark:border-gray-700">
                    <td className="px-2 py-1">{i.item_code} {i.item_name}</td>
                    <td className="px-2 py-1 text-center">{i.quantity_ordered}</td>
                    <td className="px-2 py-1 text-center">{i.quantity_received}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {view.notes && <div><b>{t('notes', language)}:</b> {view.notes}</div>}
          </div>
        )}
      </Modal>

      <ConfirmDialog open={!!del} onClose={()=>setDel(null)} onConfirm={remove} message={`${t('deletePO', language)} ${del?.po_number}?`}/>
    </div>
  )
}
