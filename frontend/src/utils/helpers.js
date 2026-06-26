export const fmt = (d) => {
  if (!d) return ''
  try {
    // Ensure the input is treated as UTC
    const iso = d.includes('Z') ? d : `${d}Z`
    const date = new Date(iso)
    // Convert to Cambodia timezone (Asia/Phnom_Penh)
    const tzStr = date.toLocaleString('en-US', { timeZone: 'Asia/Phnom_Penh' })
    const tzDate = new Date(tzStr)
    const pad = (n) => String(n).padStart(2, '0')
    return `${pad(tzDate.getDate())}/${pad(tzDate.getMonth() + 1)}/${tzDate.getFullYear()}, ${pad(tzDate.getHours())}:${pad(tzDate.getMinutes())}:${pad(tzDate.getSeconds())}`
  } catch { return String(d) }
}
export const fmtDate = (d) => {
  if (!d) return ''
  try {
    const iso = d.includes('Z') ? d : `${d}Z`
    const date = new Date(iso)
    const tzStr = date.toLocaleString('en-US', { timeZone: 'Asia/Phnom_Penh' })
    const tzDate = new Date(tzStr)
    const pad = (n) => String(n).padStart(2, '0')
    return `${pad(tzDate.getDate())}/${pad(tzDate.getMonth() + 1)}/${tzDate.getFullYear()}`
  } catch { return String(d) }
}
export const initials = (name='') => name.split(' ').filter(Boolean).slice(0,2).map(s=>s[0]?.toUpperCase()||'').join('')
export const errMsg = (e) => e?.response?.data?.detail || e?.message || 'Request failed'
