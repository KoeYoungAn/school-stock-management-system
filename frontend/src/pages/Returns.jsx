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
import { RETURN_CONDITIONS } from '../utils/constants.js'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { useValidation } from '../hooks/useValidation.js'
import { required, selectRequired, positiveNumber } from '../utils/validation.js'

const returnSchema = {
  item_id: [selectRequired('Item')],
  returned_unit_id: [selectRequired('Unit')],
  quantity_returned: [required('Quantity'), positiveNumber('Quantity')],
  received_by: [required('Received By')]
}

const blank = { item_id:'', returned_unit_id:'', quantity_returned:1, return_reason:'', condition:'Good', received_by:'', notes:'' }

export default function Returns() {
  const { user } = useAuth(); const toast = useToast()
  const { language } = useLanguage()
  const [rows,setRows]=useState([]); const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1); const [limit,setLimit]=useState(20)
  const [loading,setLoading]=useState(false)
  const [open,setOpen]=useState(false); const [edit,setEdit]=useState(null)
  const [form,setForm]=useState(blank); const [del,setDel]=useState(null)
  const [items,setItems]=useState([])
  const [units, setUnits] = useState([])
  const [selectedItemDetails, setSelectedItemDetails] = useState(null)
  const { errors, validateAll, handleBlur, clearErrors, hasErrors } = useValidation(returnSchema)
  const load=async()=>{setLoading(true);try{const r=await api.get('/api/returns',{params:{page,limit}});setRows(r.data.items);setTotal(r.data.total)}catch(e){toast.error(errMsg(e))}finally{setLoading(false)}}
  useEffect(()=>{load()},[page,limit])
  useEffect(()=>{
    api.get('/api/inventory?limit=500').then(r=>setItems(r.data.items)).catch(()=>{})
    api.get('/api/units?limit=200').then(r=>setUnits(r.data.items)).catch(()=>{})
  },[])

  // Fetch item details with conversions when item_id changes
  useEffect(() => {
    if (form.item_id) {
      api.get(`/api/inventory/${form.item_id}`).then(r => {
        setSelectedItemDetails(r.data)
        // Auto-select base unit if no unit selected yet
        if (!form.returned_unit_id && r.data.base_unit_id) {
          setForm(prev => ({ ...prev, returned_unit_id: r.data.base_unit_id }))
        }
      }).catch(() => setSelectedItemDetails(null))
    } else {
      setSelectedItemDetails(null)
    }
  }, [form.item_id])

  const openNew=()=>{setEdit(null);setForm(blank);setSelectedItemDetails(null);clearErrors();setOpen(true)}
  const openEdit=(r)=>{setEdit(r);setForm({...blank,...r,returned_unit_id:r.returned_unit_id||''});clearErrors();setOpen(true)}
  const submit=async(e)=>{
    e.preventDefault()
    const { isValid } = validateAll(form)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try{
      const payload={...form,item_id:Number(form.item_id),returned_unit_id:Number(form.returned_unit_id),quantity_returned:Number(form.quantity_returned)}
      if(edit) await api.put(`/api/returns/${edit.id}`,payload)
      else {
        const res = await api.post('/api/returns',payload)
        if (res.data.conversion_display && res.data.added_to_stock !== undefined) {
          const stockMsg = res.data.added_to_stock ? ' (added to stock)' : ' (not added to stock - damaged)'
          toast.success(`Return created: ${res.data.conversion_display}${stockMsg}`)
        } else {
          toast.success('Return created')
        }
      }
      setOpen(false);load()
    }catch(e){toast.error(errMsg(e))}
  }
  const remove=async()=>{try{await api.delete(`/api/returns/${del.id}`);toast.success('Deleted');setDel(null);load()}catch(e){toast.error(errMsg(e))}}
  const canEdit=can(user,'manage_returns'), canDelete=can(user,'delete_critical')
  const columns=[
    { key:'return_number', label:t('returnNumber', language) },
    { key:'item_name', label:t('item', language), render:r=>`${r.item_code||''} ${r.item_name||''}` },
    { key:'quantity_returned', label:t('qty', language), render:r=> {
      if (r.returned_quantity_display && r.conversion_factor > 1) {
        return <span title={`${r.returned_quantity_display} ${r.returned_unit_name || 'units'} = ${r.quantity_returned} base units`}>
          {r.returned_quantity_display} {r.returned_unit_name || 'units'} ({r.quantity_returned})
        </span>
      }
      return r.quantity_returned
    }},
    { key:'condition', label:t('condition', language), render:r=> <StatusBadge value={r.condition}/> },
    { key:'received_by', label:t('name', language) },
    { key:'date_returned', label:t('date', language), render:r=>fmtDate(r.date_returned) },
    ...(canEdit||canDelete ? [{ key:'_a', label:t('actions', language), render:r=>(
      <div className="flex gap-2">
        {canEdit && <button onClick={()=>openEdit(r)} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700" title={t('edit', language)}><Pencil className="w-4 h-4"/></button>}
        {canDelete && <button onClick={()=>setDel(r)} className="p-1 text-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900/30" title={t('delete', language)}><Trash2 className="w-4 h-4"/></button>}
      </div>
    )}]:[]),
  ]
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        {canEdit && <button onClick={openNew} className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"><Plus className="w-4 h-4"/> {t('newReturn', language)}</button>}
      </div>
      <DataTable columns={columns} rows={rows} loading={loading} emptyTitle={t('noReturns', language)}/>
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit}/>
      <Modal open={open} onClose={()=>setOpen(false)} title={edit ? t('editReturn', language) : t('newReturn', language)} size="md">
        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="sm:col-span-2">
              <SelectInput label={t('item', language)} required value={form.item_id} onChange={e=>setForm({...form,item_id:e.target.value})}
                options={[{value:'',label:'— Select —'},...items.map(i=>({value:i.id,label:`${i.item_code} ${i.item_name} (stock ${i.stock_quantity || 0})`}))]}
                error={errors.item_id} onBlur={e=>handleBlur('item_id', e.target.value)}/>
            </div>
            <SelectInput label="Unit" required value={form.returned_unit_id} onChange={e=>setForm({...form,returned_unit_id:e.target.value})}
              options={[
                {value:'',label:'— Select Unit —'},
                ...(selectedItemDetails?.base_unit ? [{value:selectedItemDetails.base_unit_id, label:`${selectedItemDetails.base_unit.name} (Base Unit)`}] : []),
                ...(selectedItemDetails?.conversions || []).map(c => ({
                  value: c.purchase_unit_id,
                  label: `${c.purchase_unit_name} (1 = ${c.conversion_factor} ${selectedItemDetails.base_unit?.abbreviation || 'units'})`
                }))
              ]}
              error={errors.returned_unit_id} onBlur={e=>handleBlur('returned_unit_id', e.target.value)}
              disabled={!selectedItemDetails}/>
            <FormInput type="number" min="1" label={t('quantity', language)} required value={form.quantity_returned} onChange={e=>setForm({...form,quantity_returned:e.target.value})}
              error={errors.quantity_returned} onBlur={e=>handleBlur('quantity_returned', e.target.value)}/>
          </div>

          {/* Conversion Preview with Return-to-Stock Indication */}
          {selectedItemDetails && form.returned_unit_id && form.quantity_returned && (() => {
            const selectedUnit = form.returned_unit_id == selectedItemDetails.base_unit_id
              ? selectedItemDetails.base_unit
              : selectedItemDetails.conversions?.find(c => c.purchase_unit_id == form.returned_unit_id)?.purchase_unit
            const conversionFactor = form.returned_unit_id == selectedItemDetails.base_unit_id
              ? 1
              : selectedItemDetails.conversions?.find(c => c.purchase_unit_id == form.returned_unit_id)?.conversion_factor || 1
            const baseQuantity = Number(form.quantity_returned) * conversionFactor
            const willAddToStock = form.condition === 'Good'

            return (
              <div className={`p-3 rounded-lg border ${willAddToStock ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700' : 'bg-gray-50 dark:bg-gray-900 border-gray-300 dark:border-gray-700'}`}>
                <div className="text-sm font-medium">
                  {conversionFactor > 1 && (
                    <div className="mb-1">{form.quantity_returned} {selectedUnit?.name || 'units'} = {baseQuantity} {selectedItemDetails.base_unit?.abbreviation || 'units'}</div>
                  )}
                  <div className={willAddToStock ? 'text-green-700 dark:text-green-300' : 'text-gray-700 dark:text-gray-300'}>
                    {willAddToStock ? '✓ Will be added to stock' : '⚠ Will NOT be added to stock (damaged)'}
                  </div>
                </div>
              </div>
            )
          })()}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <SelectInput label={t('condition', language)} value={form.condition} onChange={e=>setForm({...form,condition:e.target.value})} options={RETURN_CONDITIONS}/>
            <FormInput label={t('name', language)} required value={form.received_by||''} onChange={e=>setForm({...form,received_by:e.target.value})}
              error={errors.received_by} onBlur={e=>handleBlur('received_by', e.target.value)}/>
          </div>

          <label className="block">
            <span className="block text-sm font-medium mb-1">{t('reason', language)}</span>
            <textarea value={form.return_reason||''} onChange={e=>setForm({...form,return_reason:e.target.value})} rows="2"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
          </label>

          <div className="flex justify-end gap-2">
            <button type="button" onClick={()=>setOpen(false)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
            <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
          </div>
          <SelectInput label={t('condition', language)} value={form.condition} onChange={e=>setForm({...form,condition:e.target.value})} options={RETURN_CONDITIONS}/>
          <FormInput label={t('name', language)} required value={form.received_by||''} onChange={e=>setForm({...form,received_by:e.target.value})}
            error={errors.received_by} onBlur={e=>handleBlur('received_by', e.target.value)}/>
          <label className="sm:col-span-2 block">
            <span className="block text-sm font-medium mb-1">{t('reason', language)}</span>
            <textarea value={form.return_reason||''} onChange={e=>setForm({...form,return_reason:e.target.value})} rows="2"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
          </label>
          <div className="sm:col-span-2 flex justify-end gap-2">
            <button type="button" onClick={()=>setOpen(false)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('cancel', language)}</button>
            <button disabled={hasErrors} className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed">{t('save', language)}</button>
          </div>
        </form>
      </Modal>
      <ConfirmDialog open={!!del} onClose={()=>setDel(null)} onConfirm={remove} message={`${t('deleteReturn', language)} ${del?.return_number}?`}/>
    </div>
  )
}
