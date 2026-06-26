import React from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { can } from '../utils/permissions.js'
import AccessDenied from './AccessDenied.jsx'
export default function RoleGuard({ permission, children }) {
  const { user } = useAuth()
  if (!can(user, permission)) return <AccessDenied />
  return children
}
