import React from 'react'
import LoadingSpinner from './LoadingSpinner.jsx'
import EmptyState from './EmptyState.jsx'

/** Simple table that handles loading/empty states.
 *  columns: [{ key, label, render?(row) }]
 */
export default function DataTable({ columns, rows, loading, emptyTitle='No records' }) {
  if (loading) return <LoadingSpinner />
  if (!rows?.length) return <EmptyState title={emptyTitle} />
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
      <table className="min-w-full text-base">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            {columns.map(c => (
              <th key={c.key} className="text-left px-4 py-3.5 font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r,i) => (
            <tr key={r.id ?? i} className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/40">
              {columns.map(c => (
                <td key={c.key} className="px-4 py-3 align-middle">
                  {c.render ? c.render(r) : (r[c.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
