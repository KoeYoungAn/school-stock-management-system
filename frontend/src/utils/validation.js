/**
 * Global Form Validation Utilities
 * ──────────────────────────────────────────────────────────────────────────────
 * Reusable, framework-agnostic validation functions for the School Stock
 * Management System.  Each rule function accepts a value and a human-readable
 * field label, and returns either null (valid) or an error string (invalid).
 */

/** Trim helper – returns empty string for non-string values */
const trim = (v) => (typeof v === 'string' ? v.trim() : v)


// ── Primitive rules ──────────────────────────────────────────────────────────

/**
 * Field must not be empty / null / undefined.
 * Trims whitespace before checking.
 */
export const required = (fieldName = 'This field') => (value) => {
  const v = trim(value)
  if (v === null || v === undefined || v === '' || v === false) {
    return `${fieldName} is required`
  }
  return null
}

/**
 * Field must be a valid-looking e-mail address.
 * Skips check when the value is empty (pair with `required` for mandatory emails).
 */
export const email = (fieldName = 'Email') => (value) => {
  const v = trim(value)
  if (!v) return null // let `required` handle the empty case
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!re.test(v)) {
    return `${fieldName} must be a valid email address`
  }
  return null
}

/**
 * String value must be at least `min` characters (after trimming).
 */
export const minLength = (min, fieldName = 'This field') => (value) => {
  const v = trim(value)
  if (!v) return null // let `required` handle empty
  if (v.length < min) {
    return `${fieldName} must be at least ${min} character${min === 1 ? '' : 's'}`
  }
  return null
}

/**
 * String value must not exceed `max` characters.
 */
export const maxLength = (max, fieldName = 'This field') => (value) => {
  const v = trim(value)
  if (!v) return null
  if (v.length > max) {
    return `${fieldName} must not exceed ${max} characters`
  }
  return null
}

/**
 * Numeric value must be ≥ min.
 */
export const minValue = (min, fieldName = 'This field') => (value) => {
  if (value === null || value === undefined || value === '') return null
  if (Number(value) < min) {
    return `${fieldName} must be at least ${min}`
  }
  return null
}

/**
 * Numeric value must be > 0.
 */
export const positiveNumber = (fieldName = 'This field') => (value) => {
  if (value === null || value === undefined || value === '') return null
  if (Number(value) <= 0) {
    return `${fieldName} must be greater than 0`
  }
  return null
}

/**
 * Value must be a non-empty select (reject empty-string selects).
 */
export const selectRequired = (fieldName = 'This field') => (value) => {
  if (value === null || value === undefined || value === '' || value === 0) {
    return `${fieldName} is required – please select an option`
  }
  return null
}


// ── Composite helpers ────────────────────────────────────────────────────────

/**
 * Run a list of rule functions against a single value.
 * Returns the first error encountered, or null if all pass.
 *
 * @param {*}             value   - The form field value
 * @param {Function[]}    rules   - Array of rule functions (value) => string | null
 * @returns {string | null}
 */
export const validateField = (value, rules) => {
  if (!rules || !Array.isArray(rules)) return null
  for (const rule of rules) {
    const err = rule(value)
    if (err) return err
  }
  return null
}

/**
 * Validate an entire form data object against a schema.
 *
 * @param {Object}   data    - Key/value pairs of form data
 * @param {Object}   schema  - { fieldName: [rule, rule, ...] }
 * @returns {{ errors: Object, isValid: boolean }}
 */
export const validateForm = (data, schema) => {
  const errors = {}
  let isValid = true

  for (const [field, rules] of Object.entries(schema)) {
    const error = validateField(data[field], rules)
    if (error) {
      errors[field] = error
      isValid = false
    } else {
      errors[field] = null
    }
  }

  return { errors, isValid }
}
