import React, { useEffect, useState } from 'react'
import api from '../api/api.js'
import DataTable from '../components/DataTable.jsx'
import Pagination from '../components/Pagination.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import { useToast } from '../components/Toast.jsx'
import { errMsg, fmt } from '../utils/helpers.js'

export default function AuditLogs() {
  const toast = useToast()
  const { language } = useLanguage()
  const [rows,setRows]=useState([]); const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1); const [limit,setLimit]=useState(20)
  const [search,setSearch]=useState(''); const [module,setModule]=useState(''); const [action,setAction]=useState('')
  const [date_from,setFrom]=useState(''); const [date_to,setTo]=useState('')
  const [loading,setLoading]=useState(false)
  const load=async()=>{
    setLoading(true)
    try{const r=await api.get('/api/audit-logs',{params:{page,limit,search,module,action,date_from,date_to}}); setRows(r.data.items); setTotal(r.data.total)}
    catch(e){toast.error(errMsg(e))} finally{setLoading(false)}
  }
  useEffect(()=>{load()},[page,limit,module,action,date_from,date_to])
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <input value={search} onChange={e=>setSearch(e.target.value)} onKeyDown={e=>e.key==='Enter'&&(setPage(1),load())}
          placeholder={t('search', language)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
        <input value={module} onChange={e=>setModule(e.target.value)} placeholder={t('tableName', language)}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
        <input value={action} onChange={e=>setAction(e.target.value)} placeholder={t('action', language)}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
        <input type="date" value={date_from} onChange={e=>setFrom(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
        <input type="date" value={date_to} onChange={e=>setTo(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"/>
        <button onClick={load} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600">{t('apply', language)}</button>
      </div>
      <DataTable columns={[
        { key:'created_at', label:t('date', language), render:r=>fmt(r.created_at) },
        { key:'user_name', label:t('users', language) },
        { key:'module', label:t('tableName', language) },
        { key:'action', label:t('action', language) },
        { key:'record_id', label:t('recordId', language) },
        { key:'description', label:t('description', language) },
      ]} rows={rows} loading={loading} emptyTitle={t('noAuditLogs', language)}/>
      <Pagination page={page} limit={limit} total={total} onPage={setPage} onLimit={setLimit}/>
    </div>
  )
}
