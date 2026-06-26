import React, { useState } from 'react'
import { Upload } from 'lucide-react'
export default function FileUploadInput({ label, onChange, accept='image/*', preview }) {
  const [name, setName] = useState('')
  return (
    <label className="block">
      {label && <span className="block text-base font-medium mb-2">{label}</span>}
      <div className="flex items-center gap-4">
        {preview && <img src={preview} alt="" className="w-20 h-20 rounded-lg object-cover border border-gray-200 dark:border-gray-700" />}
        <label className="cursor-pointer inline-flex items-center gap-2 px-5 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">
          <Upload className="w-5 h-5" /> Choose file
          <input type="file" accept={accept} className="hidden" onChange={(e) => {
            const f = e.target.files?.[0]; setName(f?.name || ''); onChange?.(f)
          }} />
        </label>
        <span className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[250px]">{name}</span>
      </div>
    </label>
  )
}
