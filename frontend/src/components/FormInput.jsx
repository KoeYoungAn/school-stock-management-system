import React from 'react'

export default function FormInput({
  label,
  error,
  className = '',
  required,
  ...rest
}) {
  const hasError = error && error.trim() !== ''

  return (
    <label className="block w-full">
      {label && (
        <span className="block text-base font-medium mb-2 text-gray-700 dark:text-gray-300">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </span>
      )}
      <input
        {...rest}
        required={required}
        aria-invalid={hasError ? 'true' : 'false'}
        aria-describedby={hasError ? `${rest.name}-error` : undefined}
        className={`w-full px-4 py-3 text-base rounded-lg border bg-white dark:bg-gray-900 transition-colors
          focus:outline-none focus:ring-2
          ${hasError
            ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
            : 'border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-blue-500/20'
          } ${className}`}
      />
      {hasError && (
        <span
          id={`${rest.name}-error`}
          className="text-sm text-red-600 mt-1.5 block font-medium"
          role="alert"
        >
          {error}
        </span>
      )}
    </label>
  )
}
