import React from 'react'
export default function SummaryCard({ label, value, icon: Icon, color='blue' }) {
  const colors = {
    blue: 'bg-blue-500', green: 'bg-emerald-500', red: 'bg-red-500',
    amber: 'bg-amber-500', purple: 'bg-purple-500', gray: 'bg-gray-500',
  }
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 flex items-center gap-5 border border-gray-100 dark:border-gray-700">
      {Icon && <div className={`${colors[color]||colors.blue} text-white p-4 rounded-xl`}><Icon className="w-8 h-8" /></div>}
      <div>
        <div className="text-base text-gray-500 dark:text-gray-400">{label}</div>
        <div className="text-3xl font-semibold mt-1">{value}</div>
      </div>
    </div>
  )
}
