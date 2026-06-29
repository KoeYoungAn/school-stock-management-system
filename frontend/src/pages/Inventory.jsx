import React, { useEffect, useState } from 'react'
import api, { UPLOAD_BASE } from '../api/api.js'
import DataTable from '../components/DataTable.jsx'
import Pagination from '../components/Pagination.jsx'
import Modal from '../components/Modal.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import FormInput from '../components/FormInput.jsx'
import SelectInput from '../components/SelectInput.jsx'
import FileUploadInput from '../components/FileUploadInput.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import { useToast } from '../components/Toast.jsx'
import { can } from '../utils/permissions.js'
import { errMsg, fmtDate } from '../utils/helpers.js'
import { ITEM_CATEGORIES } from '../utils/constants.js'
import { Plus, Pencil, Trash2, Search, Eye } from 'lucide-react'
import { useValidation } from '../hooks/useValidation.js'
import { required, minLength, minValue } from '../utils/validation.js'

const blank = { item_name:'', category:'Stationery', base_unit_id:'', supplier_id:'', stock_quantity:0, minimum_stock:0, storage_location:'', condition:'Good', notes:'', conversions:[] }

const inventorySchema = {
  item_name: [required('Item Name'), minLength(2, 'Item Name')],
  base_unit_id: [required('Base Unit')],
  stock_quantity: [required('Initial Stock'), minValue(0, 'Initial Stock')],
  minimum_stock: [required('Minimum Stock'), minValue(0, 'Minimum Stock')]
}

export default function Inventory() {
  const { user } = useAuth()
  const { language } = useLanguage()
  const toast = useToast()
  const [rows, setRows] = useState([]); const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1); const [limit, setLimit] = useState(20)
  const [search, setSearch] = useState(''); const [category, setCategory] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false); const [edit, setEdit] = useState(null)
  const [form, setForm] = useState(blank); const [imgFile, setImgFile] = useState(null)
  const [del, setDel] = useState(null)
  const [viewDetail, setViewDetail] = useState(null)
  const [suppliers, setSuppliers] = useState([])
  const [units, setUnits] = useState([])
  const { errors, validateAll, handleBlur, clearErrors, hasErrors } = useValidation(inventorySchema)

  const load = async () => {
    setLoading(true)
    try {
      const r = await api.get('/api/inventory', { params: { page, limit, search, category, status } })
      setRows(r.data.items); setTotal(r.data.total)
    } catch (e) { toast.error(errMsg(e)) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [page, limit, status, category])
  useEffect(() => {
    api.get('/api/suppliers?limit=200').then(r => setSuppliers(r.data.items)).catch(()=>{})
    api.get('/api/units?limit=200').then(r => setUnits(r.data.items)).catch(()=>{})
  }, [])

  const openNew = () => { setEdit(null); setForm(blank); setImgFile(null); clearErrors(); setOpen(true) }
  const openEdit = (r) => {
    setEdit(r)
    setForm({
      ...r,
      supplier_id: r.supplier_id || '',
      base_unit_id: r.base_unit_id || '',
      conversions: r.conversions || []
    })
    setImgFile(null); clearErrors(); setOpen(true)
  }
  const submit = async (e) => {
    e.preventDefault()
    const { isValid } = validateAll(form)
    if (!isValid) { toast.error('Please fix validation errors'); return }
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k,v]) => {
        if (edit && k === 'stock_quantity') return
        if (k === 'conversions') {
          // Send conversions as JSON string
          fd.append(k, JSON.stringify(v || []))
        } else if (v !== null && v !== undefined) {
          fd.append(k, v)
        }
      })
      if (imgFile) fd.append('image', imgFile)
      if (edit) await api.put(`/api/inventory/${edit.id}`, fd)
      else await api.post('/api/inventory', fd)
      toast.success('Saved')
      setOpen(false); load()
    } catch (e) { toast.error(errMsg(e)) }
  }
  const remove = async () => {
    try { await api.delete(`/api/inventory/${del.id}`); toast.success('Deleted'); setDel(null); load() }
    catch (e) { toast.error(errMsg(e)) }
  }

  const canEdit = can(user, 'manage_inventory')
  const canDelete = can(user, 'delete_critical')

  const columns = [
    { key:'item_image', label:t('image', language), render:r => r.item_image
        ? <img src={`${UPLOAD_BASE}/${r.item_image}`} alt="" className="w-14 h-14 rounded object-cover" />
        : <div className="w-14 h-14 rounded bg-gray-200 dark:bg-gray-700" /> },
    { key:'item_code', label:t('code', language) },
    { key:'item_name', label:t('item', language) },
    { key:'category', label:t('category', language) },
    { key:'base_unit', label:t('unit', language), render:r => r.base_unit ? r.base_unit.name : (r.unit || '—') },
    { key:'stock_quantity', label:t('stock', language) },
    { key:'minimum_stock', label:t('min', language) },
    { key:'stock_status', label:t('status', language), render:r => <StatusBadge value={r.stock_status} /> },
    { key:'supplier_name', label:t('supplier', language) },
    { key:'_a', label:t('actions', language), render:r => (
      <div className="flex gap-2">
        <button onClick={()=>setViewDetail(r)} className="p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 text-blue-600" title={t('viewDetails', language)}>
          <Eye className="w-5 h-5" />
        </button>
        {canEdit && <button onClick={()=>openEdit(r)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title={t('edit', language)}>
          <Pencil className="w-5 h-5" />
        </button>}
        {canDelete && <button onClick={()=>setDel(r)} className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 text-red-600" title={t('delete', language)}>
          <Trash2 className="w-5 h-5" />
        </button>}
      </div>
    )},
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3 top-3.5 text-gray-400" />
          <input value={search} onChange={e=>setSearch(e.target.value)}
            onKeyDown={e=>e.key==='Enter' && (setPage(1), load())}
            placeholder={t('search', language)}
            className="pl-10 pr-4 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900" />
        </div>
        <select value={category} onChange={e=>{setCategory(e.target.value);setPage(1)}}
          className="px-4 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
          <option value="">{t('allCategories', language)}</option>
          {ITEM_CATEGORIES.map(c=> <option key={c}>{c}</option>)}
        </select>
        <select value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}
          className="px-4 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
          <option value="">{t('allStatus', language)}</option>
          <option>In Stock</option><option>Low Stock</option>
        </select>
        <button onClick={()=>{setPage(1);load()}} className="px-4 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800">{t('apply', language)}</button>
        <div className="ml-auto" />
        {canEdit && <button onClick={openNew}
          className="inline-flex items-center gap-2 px-4 py-3 text-base rounded-lg bg-blue-600 text-white hover:bg-blue-700">
          <Plus className="w-5 h-5"/> {t('newItem', language)}
        </button>}
      </div>
      <DataTable columns={columns} rows={rows} loading={loading} emptyTitle={t('noInventoryItems', language)} />
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit} />

      <Modal open={open} onClose={()=>setOpen(false)} title={edit ? t('editItem', language) : t('newItem', language)} size="lg">
        <form onSubmit={submit} className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <FormInput label={t('itemName', language)} required value={form.item_name} onChange={e=>setForm({...form,item_name:e.target.value})}
            error={errors.item_name} onBlur={e=>handleBlur('item_name', e.target.value)}/>
          <SelectInput label={t('category', language)} value={form.category} onChange={e=>setForm({...form,category:e.target.value})}
            options={ITEM_CATEGORIES} />
          <SelectInput label={t('baseUnit', language)} value={form.base_unit_id} onChange={e=>setForm({...form,base_unit_id:Number(e.target.value)})}
            options={units.map(u=>({value:u.id,label:`${u.name} (${u.abbreviation})`}))} error={errors.base_unit_id} />
          <SelectInput label={t('supplier', language)} value={form.supplier_id} onChange={e=>setForm({...form,supplier_id:e.target.value})}
            options={[{value:'',label:'— None —'}, ...suppliers.map(s=>({value:s.id,label:s.supplier_name}))]} />
          {!edit && <FormInput type="number" label={t('initialStock', language)} min="0" value={form.stock_quantity} onChange={e=>setForm({...form,stock_quantity:Number(e.target.value)})}
            error={errors.stock_quantity} onBlur={e=>handleBlur('stock_quantity', e.target.value)}/>}
          <FormInput type="number" label={t('minimumStock', language)} min="0" value={form.minimum_stock} onChange={e=>setForm({...form,minimum_stock:Number(e.target.value)})}
            error={errors.minimum_stock} onBlur={e=>handleBlur('minimum_stock', e.target.value)}/>
          <FormInput label={t('storageLocation', language)} value={form.storage_location||''} onChange={e=>setForm({...form,storage_location:e.target.value})}/>
          <SelectInput label={t('condition', language)} value={form.condition} onChange={e=>setForm({...form,condition:e.target.value})}
            options={['Good','Damaged']} />
          <div className="sm:col-span-2"><FileUploadInput label={t('itemImage', language)} onChange={setImgFile}
            preview={edit?.item_image ? `${UPLOAD_BASE}/${edit.item_image}` : null}/></div>

          {/* Purchase Unit Conversions */}
          <div className="sm:col-span-2">
            <label className="block text-base font-medium mb-2">Purchase Unit Conversions (Optional)</label>
            <div className="space-y-2">
              {(form.conversions || []).map((conv, idx) => (
                <div key={idx} className="flex gap-2 items-start">
                  <select
                    value={conv.purchase_unit_id}
                    onChange={e => {
                      const updated = [...form.conversions]
                      updated[idx].purchase_unit_id = Number(e.target.value)
                      setForm({...form, conversions: updated})
                    }}
                    className="flex-1 px-3 py-2 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"
                  >
                    <option value="">Select Unit</option>
                    {units.map(u => <option key={u.id} value={u.id}>{u.name} ({u.abbreviation})</option>)}
                  </select>
                  <input
                    type="number"
                    min="1"
                    placeholder="Factor"
                    value={conv.conversion_factor || ''}
                    onChange={e => {
                      const updated = [...form.conversions]
                      updated[idx].conversion_factor = Number(e.target.value)
                      setForm({...form, conversions: updated})
                    }}
                    className="w-24 px-3 py-2 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const updated = form.conversions.filter((_, i) => i !== idx)
                      setForm({...form, conversions: updated})
                    }}
                    className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 text-red-600"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => {
                  setForm({...form, conversions: [...(form.conversions || []), {purchase_unit_id: '', conversion_factor: 1, is_default_purchase_unit: false}]})
                }}
                className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <Plus className="w-4 h-4" /> Add Conversion
              </button>
            </div>
          </div>

          <label className="sm:col-span-2 block">
            <span className="block text-base font-medium mb-2">{t('notes', language)}</span>
            <textarea value={form.notes||''} onChange={e=>setForm({...form,notes:e.target.value})}
              className="w-full px-4 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900" rows="3"/>
          </label>
          <div className="sm:col-span-2 flex justify-end gap-3 mt-3">
            <button type="button" onClick={()=>setOpen(false)} className="px-5 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800">{t('cancel', language)}</button>
            <button disabled={hasErrors} className="px-5 py-3 text-base rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">{t('saveItem', language)}</button>
          </div>
        </form>
      </Modal>
      <ConfirmDialog open={!!del} onClose={()=>setDel(null)} onConfirm={remove}
        message={`${t('deleteItem', language)} "${del?.item_name}"?`} />

      <Modal open={!!viewDetail} onClose={()=>setViewDetail(null)} title={t('itemDetails', language)} size="lg">
        {viewDetail && (
          <div className="space-y-6">
            <div className="flex items-start gap-6">
              {viewDetail.item_image ? (
                <img src={`${UPLOAD_BASE}/${viewDetail.item_image}`} alt={viewDetail.item_name}
                  className="w-32 h-32 rounded-lg object-cover border border-gray-200 dark:border-gray-700" />
              ) : (
                <div className="w-32 h-32 rounded-lg bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-gray-400">
                  {t('noImage', language)}
                </div>
              )}
              <div className="flex-1">
                <h3 className="text-2xl font-semibold mb-2">{viewDetail.item_name}</h3>
                <div className="flex items-center gap-3 mb-3">
                  <StatusBadge value={viewDetail.stock_status} />
                  <span className="text-sm text-gray-500 dark:text-gray-400">{t('code', language)}: {viewDetail.item_code}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('category', language)}</label>
                <div className="text-base font-medium">{viewDetail.category}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('unit', language)}</label>
                <div className="text-base font-medium">{viewDetail.base_unit ? `${viewDetail.base_unit.name} (${viewDetail.base_unit.abbreviation})` : (viewDetail.unit || '—')}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('stockQuantity', language)}</label>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{viewDetail.stock_quantity}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('minimumStock', language)}</label>
                <div className="text-2xl font-bold text-gray-700 dark:text-gray-300">{viewDetail.minimum_stock}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('storageLocation', language)}</label>
                <div className="text-base font-medium">{viewDetail.storage_location || '—'}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('condition', language)}</label>
                <StatusBadge value={viewDetail.condition} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('supplier', language)}</label>
                <div className="text-base font-medium">{viewDetail.supplier_name || '—'}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('createdAt', language)}</label>
                <div className="text-base font-medium">{viewDetail.created_at ? fmtDate(viewDetail.created_at) : '—'}</div>
              </div>
            </div>

            {viewDetail.conversions && viewDetail.conversions.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Purchase Unit Conversions</label>
                <div className="space-y-2">
                  {viewDetail.conversions.map(conv => (
                    <div key={conv.id} className="flex items-center gap-2 text-base p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <span className="font-medium">1 {conv.purchase_unit_name}</span>
                      <span>=</span>
                      <span className="font-medium">{conv.conversion_factor} {viewDetail.base_unit?.name || 'units'}</span>
                      {viewDetail.stock_quantity > 0 && (
                        <span className="ml-auto text-sm text-gray-600 dark:text-gray-400">
                          (≈ {Math.floor(viewDetail.stock_quantity / conv.conversion_factor)} {conv.purchase_unit_name})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

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
                  {t('editItem', language)}
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
