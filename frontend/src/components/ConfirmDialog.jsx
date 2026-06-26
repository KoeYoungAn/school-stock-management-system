import React from 'react'
import Modal from './Modal.jsx'
export default function ConfirmDialog({ open, onClose, onConfirm, title='Confirm', message='Are you sure?', confirmText='Delete', danger=true }) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <p className="text-base text-gray-600 dark:text-gray-300 mb-6">{message}</p>
      <div className="flex justify-end gap-3">
        <button onClick={onClose} className="px-5 py-3 text-base rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">Cancel</button>
        <button onClick={onConfirm} className={`px-5 py-3 text-base rounded-lg text-white ${danger?'bg-red-600 hover:bg-red-700':'bg-blue-600 hover:bg-blue-700'}`}>{confirmText}</button>
      </div>
    </Modal>
  )
}
