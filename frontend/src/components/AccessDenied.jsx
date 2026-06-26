import React from 'react'
import { Lock } from 'lucide-react'
import { Link } from 'react-router-dom'
export default function AccessDenied() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <Lock className="w-12 h-12 mx-auto text-red-500 mb-3" />
        <h1 className="text-2xl font-semibold mb-2">Access Denied</h1>
        <p className="text-gray-500 dark:text-gray-400 mb-4">You don't have permission to view this page.</p>
        <Link to="/" className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700">Back to Dashboard</Link>
      </div>
    </div>
  )
}
