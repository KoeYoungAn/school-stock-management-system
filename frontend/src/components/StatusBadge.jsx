import React from 'react'

const COLORS = {
  Active: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  Inactive: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  'In Stock': 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  'Low Stock': 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  'Out of Stock': 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  Pending: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  Assigned: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  Completed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  Draft: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  Sent: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300',
  Approved: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  'Partially Received': 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  Received: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  Good: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  Damaged: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  Admin: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  Storekeeper: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  Teacher: 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
  IN: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  OUT: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  ADJUSTMENT: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
}

export default function StatusBadge({ value }) {
  const cls = COLORS[value] || 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  return <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${cls}`}>{value || '—'}</span>
}
