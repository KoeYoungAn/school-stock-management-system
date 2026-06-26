import React from 'react'
import { Inbox } from 'lucide-react'
export default function EmptyState({ title='No data', subtitle='' }) {
  return (
    <div className="text-center py-16 text-gray-500 dark:text-gray-400">
      <Inbox className="w-14 h-14 mx-auto mb-4 opacity-60" />
      <div className="font-medium text-lg">{title}</div>
      {subtitle && <div className="text-base mt-2">{subtitle}</div>}
    </div>
  )
}
