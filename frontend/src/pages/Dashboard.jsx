import React, { useEffect, useState } from 'react'
import api from '../api/api.js'
import SummaryCard from '../components/SummaryCard.jsx'
import { Boxes, AlertTriangle, ClipboardList, ShoppingCart, Truck, Building2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { useLanguage } from '../context/LanguageContext.jsx'
import { t } from '../utils/translations.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

export default function Dashboard() {
  const { user } = useAuth()
  const { language } = useLanguage()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const d = {}
        const inv = await api.get('/api/inventory?limit=1000')
        d.items = inv.data.items
        d.totalItems = inv.data.total
        d.totalStock = d.items.reduce((s,i)=>s+(i.stock_quantity||0),0)
        d.lowStock = d.items.filter(i=>i.stock_status==='Low Stock').length
        if (user.role !== 'Teacher') {
          d.suppliers = (await api.get('/api/suppliers?limit=1')).data.total
          d.departments = (await api.get('/api/departments?limit=1')).data.total
          d.pos = (await api.get('/api/purchase-orders?limit=1')).data.total
        }
        d.assignments = (await api.get('/api/assignments?limit=5')).data.items
        setData(d)
      } finally { setLoading(false) }
    })()
  }, [])

  if (loading) return <LoadingSpinner />
  if (!data) return null
  const isTeacher = user.role === 'Teacher'

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <SummaryCard label={t('totalItems', language)} value={data.totalItems} icon={Boxes} color="blue" />
        <SummaryCard label={t('totalStock', language)} value={data.totalStock} icon={Boxes} color="green" />
        <SummaryCard label={t('lowStock', language)} value={data.lowStock} icon={AlertTriangle} color="red" />
        {!isTeacher && <SummaryCard label={t('purchaseOrders', language)} value={data.pos} icon={ShoppingCart} color="purple" />}
        {!isTeacher && <SummaryCard label={t('suppliers', language)} value={data.suppliers} icon={Truck} color="amber" />}
        {!isTeacher && <SummaryCard label={t('departments', language)} value={data.departments} icon={Building2} color="gray" />}
        {isTeacher && <SummaryCard label={t('myAssignments', language)} value={data.assignments.length} icon={ClipboardList} color="purple" />}
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="font-semibold text-lg mb-4">{t('recentAssignments', language)}</h3>
        {data.assignments.length === 0 ? (
          <div className="text-base text-gray-500">{t('noRecentAssignments', language)}</div>
        ) : (
          <ul className="divide-y divide-gray-100 dark:divide-gray-700">
            {data.assignments.map(a => (
              <li key={a.id} className="py-3 flex justify-between items-center">
                <div>
                  <div className="font-medium text-base">{a.assign_number} — {a.item_name}</div>
                  <div className="text-sm text-gray-500 mt-1">{a.assign_type}: {a.target_name || '—'} · qty {a.quantity}</div>
                </div>
                <StatusBadge value={a.status} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
