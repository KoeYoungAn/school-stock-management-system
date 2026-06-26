import React from 'react'
export default function Pagination({ page, limit, total, onPage, onLimit }) {
  const pages = Math.max(1, Math.ceil(total / limit))
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 mt-4 text-base">
      <div className="text-gray-500 dark:text-gray-400">Total: {total}</div>
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2">
          <span className="text-gray-600 dark:text-gray-400">Rows:</span>
          <select value={limit} onChange={(e)=>onLimit(Number(e.target.value))}
                  className="px-3 py-2 text-base rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900">
            {[10,20,50,100].map(n=> <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
        <button disabled={page<=1} onClick={()=>onPage(page-1)}
                className="px-4 py-2 text-base rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-800">Prev</button>
        <span className="text-base">Page {page} of {pages}</span>
        <button disabled={page>=pages} onClick={()=>onPage(page+1)}
                className="px-4 py-2 text-base rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-800">Next</button>
      </div>
    </div>
  )
}
