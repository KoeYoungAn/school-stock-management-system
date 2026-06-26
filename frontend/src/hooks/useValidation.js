import { useState, useCallback } from 'react'
import { validateField, validateForm } from '../utils/validation'

/**
 * React hook for form validation
 * 
 * @param {Object} schema - Validation schema { fieldName: [rules...] }
 * @returns {Object} Validation state and methods
 */
export const useValidation = (schema) => {
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})

  /**
   * Validate a single field
   */
  const validateSingleField = useCallback((name, value) => {
    const rules = schema[name]
    if (!rules) return null
    
    const error = validateField(value, rules)
    
    setErrors(prev => ({
      ...prev,
      [name]: error
    }))
    
    return error
  }, [schema])

  /**
   * Validate all fields in the form
   */
  const validateAll = useCallback((values) => {
    const result = validateForm(values, schema)
    setErrors(result.errors)
    return result
  }, [schema])

  /**
   * Handle field blur event
   */
  const handleBlur = useCallback((name, value) => {
    setTouched(prev => ({ ...prev, [name]: true }))
    validateSingleField(name, value)
  }, [validateSingleField])

  /**
   * Clear all errors and touched state
   */
  const clearErrors = useCallback(() => {
    setErrors({})
    setTouched({})
  }, [])

  /**
   * Clear error for a specific field
   */
  const clearFieldError = useCallback((name) => {
    setErrors(prev => {
      const newErrors = { ...prev }
      delete newErrors[name]
      return newErrors
    })
  }, [])

  /**
   * Check if there are any errors
   */
  const hasErrors = Object.values(errors).some(e => e !== null && e !== undefined && e !== '')

  /**
   * Get error for a field only if it's been touched
   */
  const getFieldError = useCallback((name) => {
    return touched[name] ? errors[name] : null
  }, [errors, touched])

  return {
    errors,
    touched,
    validateSingleField,
    validateAll,
    handleBlur,
    clearErrors,
    clearFieldError,
    hasErrors,
    getFieldError
  }
}
