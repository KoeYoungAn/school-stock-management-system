import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
export const UPLOAD_BASE = `${API_BASE}/uploads`

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
})

export default api
