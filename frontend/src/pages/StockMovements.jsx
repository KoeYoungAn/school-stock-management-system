import React, { useEffect, useState } from 'react'
import api from '../api/api.js'
import DataTable from '../components/DataTable.jsx'
import Pagination from '../components/Pagination.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import { useToast } from '../components/Toast.jsx'
import { errMsg, fmt } from '../utils/helpers.js'

export default function StockMovements() {
  const toast = useToast()
  const { language } = useLanguage()
  const [rows,setRows]=useState([]); const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1); const [limit,setLimit]=useState(20)
  const [movement_type,setMt]=useState(''); const [loading,setLoading]=useState(false)
  const load=async()=>{
    setLoading(true)
    try{const r=await api.get('/api/stock-movements',{params:{page,limit,movement_type}});setRows(r.data.items);setTotal(r.data.total)}
    catch(e){toast.error(errMsg(e))}finally{setLoading(false)}
  }
  useEffect(()=>{load()},[page,limit,movement_type])
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <select value={movement_type} onChange={e=>{setMt(e.target.value);setPage(1)}}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
          <option value="">{t('type', language)}</option><option>IN</option><option>OUT</option><option>ADJUSTMENT</option>
        </select>
      </div>
      <DataTable columns={[
        { key:'created_at', label:t('date', language), render:r=>fmt(r.created_at) },
        { key:'item_name', label:t('item', language), render:r=>`${r.item_code||''} ${r.item_name||''}` },
        { key:'movement_type', label:t('type', language), render:r=> <StatusBadge value={r.movement_type}/> },
        { key:'quantity', label:t('qty', language) },
        { key:'balance_after', label:t('stock', language) },
        { key:'source_type', label:t('type', language) },
        { key:'notes', label:t('notes', language) },
      ]} rows={rows} loading={loading} emptyTitle={t('noMovements', language)}/>
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit}/>
    </div>
  )
}
