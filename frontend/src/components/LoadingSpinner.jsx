import React from 'react'
export default function LoadingSpinner({ label='Loading...' }) {
  return (
    <div className="flex items-center justify-center py-16 text-gray-500 dark:text-gray-400">
      <div className="w-8 h-8 border-3 border-gray-300 border-t-blue-600 rounded-full animate-spin mr-4" />
      <span className="text-base">{label}</span>
    </div>
  )
}
