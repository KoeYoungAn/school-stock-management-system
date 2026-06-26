import React, { useMemo, useState } from 'react'
import api from '../api/api.js'
import SelectInput from '../components/SelectInput.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../components/Toast.jsx'
import { errMsg, fmtDate, fmt } from '../utils/helpers.js'
import { ITEM_CATEGORIES } from '../utils/constants.js'
import {
  ChevronDown, Download, FileDown, FileSpreadsheet, Printer, TrendingUp
} from 'lucide-react'

const REPORT_TYPES = [
  { value: 'inventory-summary', label: 'Inventory Summary Report', endpoint: '/api/reports/stock-summary' },
  { value: 'low-stock', label: 'Low Stock Report', endpoint: '/api/reports/stock-summary', fixedStatus: 'Low Stock' },
  { value: 'out-of-stock', label: 'Out of Stock Report', endpoint: '/api/reports/stock-summary', fixedStatus: 'Out of Stock' },
  { value: 'stock-movements', label: 'Stock Movement Report', endpoint: '/api/reports/stock-movements' },
  { value: 'purchase-orders', label: 'Purchase Order Report', endpoint: '/api/purchase-orders' },
  { value: 'receiving', label: 'Receiving Report', endpoint: '/api/receiving' },
  { value: 'returns', label: 'Returns Report', endpoint: '/api/returns' },
  { value: 'department-usage', label: 'Department Usage Report', endpoint: '/api/assignments' },
  { value: 'suppliers', label: 'Supplier Report', endpoint: '/api/suppliers' },
  { value: 'monthly_stock_summary', label: 'Monthly Stock Summary Report', endpoint: '/api/reports/monthly-stock-summary' },
]

const STATUS_OPTIONS = ['', 'In Stock', 'Low Stock', 'Out of Stock']
const MOVEMENT_TYPES = ['', 'IN', 'OUT', 'ADJUSTMENT']

const REPORT_COLUMNS = {
  'inventory-summary': [
    { key: 'item_code', label: 'Item Code' },
    { key: 'item_name', label: 'Item Name' },
    { key: 'category', label: 'Category' },
    { key: 'unit', label: 'Unit' },
    { key: 'stock_quantity', label: 'Stock' },
    { key: 'minimum_stock', label: 'Minimum Stock' },
    { key: 'stock_status', label: 'Status' },
  ],
  'low-stock': [
    { key: 'item_code', label: 'Item Code' },
    { key: 'item_name', label: 'Item Name' },
    { key: 'category', label: 'Category' },
    { key: 'unit', label: 'Unit' },
    { key: 'stock_quantity', label: 'Current Stock' },
    { key: 'minimum_stock', label: 'Minimum Stock' },
    { key: 'shortage', label: 'Shortage', compute: (row) => Math.max(0, (row.minimum_stock || 0) - (row.stock_quantity || 0)) },
  ],
  'out-of-stock': [
    { key: 'item_code', label: 'Item Code' },
    { key: 'item_name', label: 'Item Name' },
    { key: 'category', label: 'Category' },
    { key: 'unit', label: 'Unit' },
    { key: 'stock_quantity', label: 'Current Stock' },
    { key: 'stock_status', label: 'Status' },
  ],
  'stock-movements': [
    { key: 'created_at', label: 'Date' },
    { key: 'item_code', label: 'Item Code' },
    { key: 'item_name', label: 'Item Name' },
    { key: 'movement_type', label: 'Movement Type' },
    { key: 'source_type', label: 'Reference Type' },
    { key: 'quantity', label: 'Quantity' },
    { key: 'balance_after', label: 'Balance After' },
  ],
  'purchase-orders': [
    { key: 'po_number', label: 'PO Number' },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'order_date', label: 'Order Date' },
    { key: 'expected_delivery_date', label: 'Expected Date' },
    { key: 'status', label: 'Status' },
    { key: 'total_items', label: 'Total Items' },
  ],
  'receiving': [
    { key: 'receiving_number', label: 'Receiving No.' },
    { key: 'item_code', label: 'Item Code' },
    { key: 'item_name', label: 'Item Name' },
    { key: 'quantity_received', label: 'Qty Received' },
    { key: 'receiver_name', label: 'Received By' },
    { key: 'status', label: 'Status' },
    { key: 'date_received', label: 'Date' },
  ],
  'returns': [
    { key: 'return_number', label: 'Return No.' },
    { key: 'item_code', label: 'Item Code' },
    { key: 'item_name', label: 'Item Name' },
    { key: 'quantity_returned', label: 'Quantity' },
    { key: 'condition', label: 'Condition' },
    { key: 'received_by', label: 'Received By' },
  ],
  'department-usage': [
    { key: 'assign_number', label: 'Assignment No.' },
    { key: 'item_code', label: 'Item Code' },
    { key: 'item_name', label: 'Item Name' },
    { key: 'quantity', label: 'Qty Assigned' },
    { key: 'assign_type', label: 'Type' },
    { key: 'status', label: 'Status' },
    { key: 'assigned_date', label: 'Date' },
  ],
  'suppliers': [
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'contact_person', label: 'Contact Person' },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: 'Phone' },
    { key: 'status', label: 'Status' },
  ],
  'monthly_stock_summary': [
    { key: 'item_code', label: 'Item Code' },
    { key: 'item_name', label: 'Item Name' },
    { key: 'category', label: 'Category' },
    { key: 'unit', label: 'Unit' },
    { key: 'opening_balance', label: 'Opening Balance' },
    { key: 'total_received', label: 'Total Received' },
    { key: 'total_issued', label: 'Total Assigned / Issued' },
    { key: 'total_returned', label: 'Total Returned' },
    { key: 'total_adjustment', label: 'Total Adjustment' },
    { key: 'closing_balance', label: 'Closing Balance' },
    { key: 'status', label: 'Status' },
  ],
}

const FILTER_CONFIG = {
  'inventory-summary': ['category', 'status'],
  'low-stock': ['category'],
  'out-of-stock': ['category'],
  'stock-movements': ['dateFrom', 'dateTo', 'movementType'],
  'purchase-orders': ['dateFrom', 'dateTo', 'status'],
  'receiving': ['dateFrom', 'dateTo', 'status'],
  'returns': ['dateFrom', 'dateTo'],
  'department-usage': ['dateFrom', 'dateTo'],
  'suppliers': ['dateFrom', 'dateTo'],
  'monthly_stock_summary': ['monthYear', 'category', 'status'],
}

const getReportColumns = (reportType) => REPORT_COLUMNS[reportType] || REPORT_COLUMNS['inventory-summary']
const emptyFilters = () => ({ category: '', status: '', dateFrom: '', dateTo: '', movementType: '', monthYear: '' })
const formatCell = (key, value) => {
  if (value === null || value === undefined || value === '') return '—'
  if (key.includes('date') || key === 'created_at') return fmtDate(value)
  return value
}

export default function Reports() {
  const { user } = useAuth()
  const toast = useToast()
  const [reportType, setReportType] = useState('inventory-summary')
  const [data, setData] = useState(null)
  const [generatedReport, setGeneratedReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [filters, setFilters] = useState(emptyFilters())

  const selectedReport = REPORT_TYPES.find(r => r.value === reportType) || REPORT_TYPES[0]
  const requiredFilters = FILTER_CONFIG[reportType] || []
  const generated = !!generatedReport && !!data
  const rows = useMemo(() => data?.items || [], [data])
  const columns = useMemo(() => getReportColumns(generatedReport?.value || reportType), [generatedReport, reportType])

  const handleReportTypeChange = (value) => {
    setReportType(value)
    setError('')
    setFilters(emptyFilters())
  }

  const buildParams = () => {
    const params = { limit: 500 }
    if (requiredFilters.includes('category') && filters.category) params.category = filters.category
    if (requiredFilters.includes('status') && filters.status) params.status = selectedReport.fixedStatus || filters.status
    if (selectedReport.fixedStatus) params.status = selectedReport.fixedStatus
    if (requiredFilters.includes('dateFrom') && filters.dateFrom) params.date_from = filters.dateFrom
    if (requiredFilters.includes('dateTo') && filters.dateTo) params.date_to = filters.dateTo
    if (requiredFilters.includes('movementType') && filters.movementType) params.movement_type = filters.movementType
    if (requiredFilters.includes('monthYear') && filters.monthYear) {
      const [year, month] = filters.monthYear.split('-')
      params.month = parseInt(month, 10)
      params.year = parseInt(year, 10)
    }
    return params
  }

  const generateReport = async () => {
    if (requiredFilters.includes('monthYear') && !filters.monthYear) {
        setError('Please select a month and year.')
        return
    }
    setLoading(true)
    setError('')
    try {
      const params = buildParams()
      const response = await api.get(selectedReport.endpoint, { params })
      setData(response.data)
      setGeneratedReport(selectedReport)
    } catch (e) {
      const message = errMsg(e)
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  const exportReport = async (type) => {
    if (!generated) return
    if (type === 'print') {
      window.print()
      return
    }
    toast.info(`${type.toUpperCase()} export will be connected after preview data is approved.`)
  }

  return (
    <div className="space-y-6 print:bg-white">
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-blue-600 text-white"><TrendingUp className="w-6 h-6" /></div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Reports</h1>
          <p className="text-gray-500 dark:text-gray-400">Generate, preview, print, and export official school reports.</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-5 shadow-sm print:hidden">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <SelectInput label="Report Type" value={reportType} onChange={e => handleReportTypeChange(e.target.value)} options={REPORT_TYPES.map(r => ({ value: r.value, label: r.label }))}/>

          {requiredFilters.includes('category') && (
            <select value={filters.category} onChange={e => setFilters(f => ({ ...f, category: e.target.value }))} className="px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
              <option value="">All Categories</option>{ITEM_CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
          )}

          {requiredFilters.includes('status') && !selectedReport.fixedStatus && (
            <select value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))} className="px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
              {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s || 'All Status'}</option>)}
            </select>
          )}

          {requiredFilters.includes('dateFrom') && (
            <input type="date" value={filters.dateFrom} onChange={e => setFilters(f => ({ ...f, dateFrom: e.target.value }))} className="px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900" />
          )}

          {requiredFilters.includes('dateTo') && (
            <input type="date" value={filters.dateTo} onChange={e => setFilters(f => ({ ...f, dateTo: e.target.value }))} className="px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900" />
          )}

          {requiredFilters.includes('movementType') && (
            <select value={filters.movementType} onChange={e => setFilters(f => ({ ...f, movementType: e.target.value }))} className="px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
              {MOVEMENT_TYPES.map(type => <option key={type} value={type}>{type || 'All Movement Types'}</option>)}
            </select>
          )}

          {requiredFilters.includes('monthYear') && (
            <input type="month" value={filters.monthYear} onChange={e => setFilters(f => ({ ...f, monthYear: e.target.value }))} className="px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900" />
          )}
        </div>

        {error && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        <div className="flex gap-3 mt-4">
          <button onClick={generateReport} disabled={loading} className="px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60">
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
          <div className="relative">
            <button onClick={() => setShowExportMenu(!showExportMenu)} disabled={!generated} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">
              Export <ChevronDown className="w-4 h-4"/>
            </button>
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-40 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10">
                <button onClick={() => { exportReport('pdf'); setShowExportMenu(false) }} className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"><FileDown className="w-4 h-4"/> PDF</button>
                <button onClick={() => { exportReport('excel'); setShowExportMenu(false) }} className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"><FileSpreadsheet className="w-4 h-4"/> Excel</button>
                <button onClick={() => { exportReport('csv'); setShowExportMenu(false) }} className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"><Download className="w-4 h-4"/> CSV</button>
                <button onClick={() => { exportReport('print'); setShowExportMenu(false) }} className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"><Printer className="w-4 h-4"/> Print</button>
              </div>
            )}
          </div>
        </div>
      </div>

      {generated && (
        <div className="mx-auto w-full max-w-5xl bg-white p-8 shadow-lg min-h-[1000px] text-gray-900 border border-gray-200 print:shadow-none print:border-0">
          <div className="text-center border-b border-gray-300 pb-5 mb-6">
            <div className="mx-auto mb-3 h-16 w-16 rounded-full border border-gray-300 flex items-center justify-center text-xs text-gray-500">Logo</div>
            <h2 className="text-xl font-bold uppercase">School Stock Management System</h2>
            <p className="text-sm text-gray-600">Official School Report</p>
            <h1 className="mt-4 text-2xl font-bold uppercase tracking-wide">{generatedReport.label}</h1>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm mb-5">
            <div><span className="font-semibold">Report Number:</span> RPT-{Date.now().toString().slice(-8)}</div>
            <div><span className="font-semibold">Generated Date:</span> {fmt(new Date().toISOString())}</div>
            <div><span className="font-semibold">Generated By:</span> {user?.full_name || user?.email || 'Current User'}</div>
            <div><span className="font-semibold">Rows:</span> {rows.length}</div>
            {generatedReport.value === 'monthly_stock_summary' && data?.metadata && (
              <>
                <div><span className="font-semibold">Month:</span> {data.metadata.month_name} {data.metadata.year}</div>
                <div><span className="font-semibold">Report Period:</span> {data.metadata.start_date} to {data.metadata.end_date}</div>
              </>
            )}
            {filters.category && <div><span className="font-semibold">Category:</span> {filters.category}</div>}
            {filters.status && <div><span className="font-semibold">Status:</span> {filters.status}</div>}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead className="bg-slate-800 text-white">
                <tr>{columns.map(col => <th key={col.key} className="border border-slate-700 px-2 py-2 text-left font-semibold">{col.label}</th>)}</tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr><td colSpan={columns.length} className="border border-gray-300 px-3 py-8 text-center text-gray-500">No records found for the selected filters.</td></tr>
                ) : rows.map((row, index) => (
                  <tr key={row.id || index} className={index % 2 ? 'bg-gray-50' : 'bg-white'}>
                    {columns.map(col => {
                      const value = col.compute ? col.compute(row) : row[col.key]
                      return <td key={col.key} className="border border-gray-300 px-2 py-2">{formatCell(col.key, value)}</td>
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-8 grid grid-cols-3 gap-8 text-center text-sm">
            <div><div className="border-t border-gray-500 pt-2 mt-16">Prepared By</div><div className="mt-3">Date: __________</div></div>
            <div><div className="border-t border-gray-500 pt-2 mt-16">Checked By</div><div className="mt-3">Date: __________</div></div>
            <div><div className="border-t border-gray-500 pt-2 mt-16">Approved By</div><div className="mt-3">Date: __________</div></div>
          </div>
        </div>
      )}
    </div>
  )
}
