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
import { RCV_STATUSES } from '../utils/constants.js'
import { Pencil, Trash2, PackageCheck, ClipboardList } from 'lucide-react'
import { useValidation } from '../hooks/useValidation.js'
import { required, selectRequired, positiveNumber } from '../utils/validation.js'

const receivingSchema = {
  purchase_order_id: [selectRequired('Purchase Order')],
  purchase_order_item_id: [selectRequired('PO Line Item')],
  item_id: [selectRequired('Item')],
  quantity_received: [required('Quantity'), positiveNumber('Quantity')],
  receiver_name: [required('Receiver Name')]
}

const blankReceivePO = { purchase_order_id:'', purchase_order_item_id:'', item_id:'', quantity_received:1, receiver_name:'', status:'Received', notes:'' }
const blankDirectReceipt = { item_id: '', quantity: 1, source: '', reason: '', receiver_name: '', notes: '' }

export default function Receiving() {
  const { user } = useAuth(); const toast = useToast()
  const { language } = useLanguage()
  const [rows,setRows]=useState([]); const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1); const [limit,setLimit]=useState(20); const [status,setStatus]=useState('')
  const [loading,setLoading]=useState(false); const [openPO,setOpenPO]=useState(false); const [edit,setEdit]=useState(null)
  const [formPO,setFormPO]=useState(blankReceivePO); const [del,setDel]=useState(null)
  const [pos,setPos]=useState([]); const [items,setItems]=useState([])
  const [directReceiptOpen, setDirectReceiptOpen] = useState(false)
  const [directReceiptForm, setDirectReceiptForm] = useState(blankDirectReceipt)

  const { errors, validateAll, handleBlur, clearErrors, hasErrors } = useValidation(receivingSchema)

  const load = async () => {
    setLoading(true)
    try{const r=await api.get('/api/receiving',{params:{page,limit,status}}); setRows(r.data.items); setTotal(r.data.total)}
    catch(e){toast.error(errMsg(e))} finally{setLoading(false)}
  }
  const loadPOs = async () => {
    const r = await api.get('/api/purchase-orders?limit=200')
    setPos(r.data.items)
  }
  useEffect(()=>{load()},[page,limit,status])
  useEffect(()=>{
    loadPOs().catch(()=>{})
    api.get('/api/inventory?limit=500').then(r=>setItems(r.data.items)).catch(()=>{})
  },[])

  const receivablePOs = pos.filter(po =>
    ['Approved', 'Partially Received'].includes(po.status) &&
    (po.items || []).some(i => (i.quantity_ordered - (i.quantity_received || 0)) > 0)
  )
  const poItems = (pos.find(p=>String(p.id)===String(formPO.purchase_order_id))?.items || [])
    .filter(i => edit || (i.quantity_ordered - (i.quantity_received || 0)) > 0)
  const selectedPOItem = poItems.find(x=>String(x.id)===String(formPO.purchase_order_item_id))
  const remainingQty = selectedPOItem ? (selectedPOItem.quantity_ordered - (selectedPOItem.quantity_received || 0)) : null

  const openReceivePO = () => { setEdit(null); setFormPO(blankReceivePO); clearErrors(); setOpenPO(true) }
  const openEdit = (r) => {
    setEdit(r)
    setFormPO({
      ...blankReceivePO,
      ...r,
      purchase_order_id: r.purchase_order_id || '',
      purchase_order_item_id: r.purchase_order_item_id || ''
    })
    clearErrors()
    setOpenPO(true)
  }

  const submitReceivePO = async (e) => {
    e.preventDefault()
    const { isValid } = validateAll(formPO)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    if (!edit && remainingQty !== null && Number(formPO.quantity_received) > remainingQty) {
      toast.error(`Cannot exceed remaining quantity (${remainingQty})`)
      return
    }
    try {
      const payload = {...formPO,
        item_id:Number(formPO.item_id),
        quantity_received:Number(formPO.quantity_received),
        purchase_order_id:Number(formPO.purchase_order_id),
        purchase_order_item_id:Number(formPO.purchase_order_item_id),
      }
      if (edit) {
        if (!confirm('Are you sure you want to correct this receiving record? This is for fixing errors in existing records.')) return
        await api.put(`/api/receiving/${edit.id}`, payload)
      } else {
        await api.post('/api/receiving', payload)
      }
      toast.success(edit ? 'Correction saved' : 'PO receiving saved')
      setOpenPO(false)
      load()
      loadPOs().catch(()=>{})
    } catch(e){toast.error(errMsg(e))}
  }

  const submitDirectReceipt = async (e) => {
    e.preventDefault()
    if (!directReceiptForm.item_id) { toast.error('Item is required'); return }
    if (!directReceiptForm.source?.trim()) { toast.error('Source is required'); return }
    if (!directReceiptForm.reason?.trim()) { toast.error('Reason is required'); return }
    if (!directReceiptForm.receiver_name?.trim()) { toast.error('Receiver Name is required'); return }
    if (Number(directReceiptForm.quantity) <= 0) { toast.error('Quantity must be greater than 0'); return }

    try {
      const payload = {
        item_id: Number(directReceiptForm.item_id),
        quantity_received: Number(directReceiptForm.quantity),
        source: directReceiptForm.source.trim(),
        reason: directReceiptForm.reason.trim(),
        receiver_name: directReceiptForm.receiver_name.trim(),
        notes: directReceiptForm.notes || ''
      }
      const r = await api.post('/api/direct-receipt', payload)
      toast.success(`Direct receipt saved. New stock: ${r.data.new_stock}`)
      setDirectReceiptOpen(false)
      setDirectReceiptForm(blankDirectReceipt)
      load()
    } catch(e) { toast.error(errMsg(e)) }
  }

  const remove = async () => {
    try{await api.delete(`/api/receiving/${del.id}`); toast.success('Deleted'); setDel(null); load(); loadPOs().catch(()=>{})}
    catch(e){toast.error(errMsg(e))}
  }

  const canEdit = can(user,'manage_receiving')
  const canDelete = can(user,'delete_critical')

  const columns = [
    { key:'receiving_number', label:t('receiveNumber', language) },
    { key:'item_name', label:t('item', language), render:r=>`${r.item_code||''} ${r.item_name||''}` },
    { key:'quantity_received', label:t('qty', language) },
    { key:'receiver_name', label:t('name', language) },
    { key:'date_received', label:t('date', language), render:r=>fmtDate(r.date_received) },
    { key:'status', label:t('status', language), render:r=> <StatusBadge value={r.status}/> },
    ...(canEdit||canDelete ? [{ key:'_a', label:t('actions', language), render:r=>(
      <div className="flex gap-2">
        {canEdit && <button onClick={()=>openEdit(r)} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700" title="Edit Record (correction only)"><Pencil className="w-4 h-4"/></button>}
        {canDelete && <button onClick={()=>setDel(r)} className="p-1 text-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900/30" title={t('delete', language)}><Trash2 className="w-4 h-4"/></button>}
      </div>
    )}]:[]),
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <select value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
          <option value="">{t('allStatus', language)}</option>{RCV_STATUSES.map(s=> <option key={s}>{s}</option>)}
        </select>
        <div className="ml-auto"/>
        {canEdit && (
          <>
            <button onClick={openReceivePO} className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700">
              <PackageCheck className="w-4 h-4"/> Receive from PO
            </button>
            <button onClick={()=>setDirectReceiptOpen(true)} className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700">
              <ClipboardList className="w-4 h-4"/> Direct Stock Receipt
            </button>
          </>
        )}
      </div>
      <DataTable columns={columns} rows={rows} loading={loading} emptyTitle={t('noReceiving', language)}/>
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit}/>

      <Modal open={openPO} onClose={()=>setOpenPO(false)} title={edit ? 'Edit Receiving Record (Correction Only)' : 'Receive from PO'} size="lg">
        <form onSubmit={submitReceivePO} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-sm text-yellow-800 dark:text-yellow-200">
            {edit ? (
              <strong>⚠️ Correction only: use this to fix an existing receiving record, not to receive more stock.</strong>
            ) : (
              <strong>📝 Receive from PO: handles first and additional receiving for approved PO line items.</strong>
            )}
          </div>
          <SelectInput label={edit ? `${t('purchaseOrder', language)} (Locked)` : t('purchaseOrder', language)}
            disabled={!!edit}
            required
            value={formPO.purchase_order_id} onChange={e=>setFormPO({...formPO,purchase_order_id:e.target.value,purchase_order_item_id:'',item_id:''})}
            options={[{value:'',label:'— Select PO —'}, ...receivablePOs.map(p=>({value:p.id,label:`${p.po_number} (${p.supplier_name})`}))]}/>
          {formPO.purchase_order_id && (
            <SelectInput label={edit ? 'PO Line Item (Locked)' : 'PO Line Item'}
              disabled={!!edit}
              required
              value={formPO.purchase_order_item_id} onChange={e=>{
                const it = poItems.find(x=>String(x.id)===e.target.value)
                setFormPO({...formPO, purchase_order_item_id:e.target.value, item_id: it?it.item_id:''})
              }}
              options={[{value:'',label:'— Select Line Item —'}, ...poItems.map(i=>({value:i.id,label:`${i.item_code} ${i.item_name} (Ordered: ${i.quantity_ordered}, Received: ${i.quantity_received || 0}, Remaining: ${i.quantity_ordered - (i.quantity_received || 0)})`}))]}/>
          )}
          <SelectInput label={edit ? `${t('item', language)} (Locked)` : `${t('item', language)} (Locked from PO line)`} required value={formPO.item_id}
            disabled={true}
            options={[{value:'',label:'— Select PO Line Item First —'}, ...items.map(i=>({value:i.id,label:`${i.item_code} ${i.item_name}`}))]}
            error={errors.item_id} onBlur={e=>handleBlur('item_id', e.target.value)}/>
          {selectedPOItem && (
            <div className="sm:col-span-2 grid grid-cols-3 gap-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
              <div><span className="text-gray-500 dark:text-gray-400">Ordered:</span><span className="ml-1 font-bold">{selectedPOItem.quantity_ordered}</span></div>
              <div><span className="text-gray-500 dark:text-gray-400">Already Received:</span><span className="ml-1 font-bold">{selectedPOItem.quantity_received || 0}</span></div>
              <div><span className="text-gray-500 dark:text-gray-400">Remaining:</span><span className="ml-1 font-bold text-blue-600 dark:text-blue-400">{remainingQty}</span></div>
            </div>
          )}
          <FormInput type="number" min="1" max={remainingQty || undefined} label={edit ? 'Corrected Quantity' : 'Quantity to Receive Now'} required value={formPO.quantity_received} onChange={e=>setFormPO({...formPO,quantity_received:e.target.value})}
            error={errors.quantity_received || (!edit && remainingQty !== null && Number(formPO.quantity_received) > remainingQty ? `Cannot exceed remaining quantity (${remainingQty})` : '')}
            onBlur={e=>handleBlur('quantity_received', e.target.value)}/>
          <FormInput label="Receiver Name" required value={formPO.receiver_name||''} onChange={e=>setFormPO({...formPO,receiver_name:e.target.value})}
            error={errors.receiver_name} onBlur={e=>handleBlur('receiver_name', e.target.value)}/>
          <SelectInput label={t('status', language)} value={formPO.status} onChange={e=>setFormPO({...formPO,status:e.target.value})} options={RCV_STATUSES}/>
          <label className="sm:col-span-2 block">
            <span className="block text-sm font-medium mb-1">{t('notes', language)}</span>
            <textarea value={formPO.notes||''} onChange={e=>setFormPO({...formPO,notes:e.target.value})} rows="2"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
          </label>
          <div className="sm:col-span-2 flex justify-end gap-2">
            <button type="button" onClick={()=>setOpenPO(false)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
            <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
          </div>
        </form>
      </Modal>

      <Modal open={directReceiptOpen} onClose={()=>setDirectReceiptOpen(false)} title="Direct Stock Receipt" size="lg">
        <form onSubmit={submitDirectReceipt} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-blue-800 dark:text-blue-200">
            <strong>📋 Direct Receipt: for opening stock, donation, emergency stock, or approved manual entry only.</strong>
          </div>
          <SelectInput label={t('item', language)} required value={directReceiptForm.item_id}
            onChange={e=>setDirectReceiptForm({...directReceiptForm,item_id:e.target.value})}
            options={[{value:'',label:'— Select Item —'}, ...items.map(i=>({value:i.id,label:`${i.item_code} ${i.item_name}`}))]}/>
          <FormInput type="number" min="1" label="Quantity" required value={directReceiptForm.quantity}
            onChange={e=>setDirectReceiptForm({...directReceiptForm,quantity:e.target.value})}/>
          <FormInput label="Source" required value={directReceiptForm.source}
            onChange={e=>setDirectReceiptForm({...directReceiptForm,source:e.target.value})}
            placeholder="e.g., Opening Stock, Donation"/>
          <FormInput label="Reason" required value={directReceiptForm.reason}
            onChange={e=>setDirectReceiptForm({...directReceiptForm,reason:e.target.value})}
            placeholder="e.g., Initial inventory"/>
          <FormInput label="Receiver Name" required value={directReceiptForm.receiver_name}
            onChange={e=>setDirectReceiptForm({...directReceiptForm,receiver_name:e.target.value})}/>
          <label className="sm:col-span-2 block">
            <span className="block text-sm font-medium mb-1">Notes</span>
            <textarea value={directReceiptForm.notes||''} onChange={e=>setDirectReceiptForm({...directReceiptForm,notes:e.target.value})} rows="2"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
          </label>
          <div className="sm:col-span-2 flex justify-end gap-2">
            <button type="button" onClick={()=>setDirectReceiptOpen(false)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">Cancel</button>
            <button className="px-3 py-2 rounded-lg bg-blue-600 text-white">Save Direct Receipt</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog open={!!del} onClose={()=>setDel(null)} onConfirm={remove} message={`${t('deleteReceiving', language)} ${del?.receiving_number}?`}/>
    </div>
  )
}
