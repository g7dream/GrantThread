const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
const TOKEN_KEY = 'grantthread.session'
export class ApiError extends Error {
  status: number
  code: string
  constructor(message: string, status: number, code = '') { super(message); this.status = status; this.code = code }
}
export function token() { return sessionStorage.getItem(TOKEN_KEY) }
export function setToken(value: string | null) { if (value) sessionStorage.setItem(TOKEN_KEY, value); else sessionStorage.removeItem(TOKEN_KEY) }
export function apiUrl(path: string) { return `${API_BASE}${path}` }
async function request(path: string, options: RequestInit = {}) {
  const response = await fetch(apiUrl(path), { ...options, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(token() ? { Authorization: `Bearer ${token()}` } : {}), ...options.headers } })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    if (response.status === 401 && path !== '/demo/login') window.dispatchEvent(new Event('grantthread:unauthorized'))
    throw new ApiError(typeof body.error === 'string' ? body.error : typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}). Please try again.`, response.status, body.code)
  }
  return response
}
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await request(path, body === undefined ? {} : { method: 'POST', body: JSON.stringify(body) })
  return response.status === 204 ? undefined as T : response.json()
}
export async function download(path: string, name: string) {
  const response = await request(path)
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url; link.download = name; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 10000)
}
export async function uploadEvidence(file: File, fields: Record<string, unknown>) {
  const contentType = file.name.toLowerCase().endsWith('.pdf') ? 'application/pdf' : 'text/plain'
  const intent = await api<{ id: string; uploadUrl: string; method: string; headers: Record<string, string> }>('/evidence/upload-intent', { ...fields, name: file.name, contentType, size: file.size })
  const target = /^https?:/.test(intent.uploadUrl) ? intent.uploadUrl : new URL(intent.uploadUrl, new URL(API_BASE, location.origin)).href
  // Bearer credentials belong only on the API's local upload route, never a signed S3 URL.
  const apiOrigin = new URL(API_BASE, location.origin).origin
  const headers = { ...intent.headers, ...(new URL(target).origin === apiOrigin && token() ? { Authorization: `Bearer ${token()}` } : {}) }
  const response = await fetch(target, { method: intent.method, headers, body: file })
  if (!response.ok) throw new ApiError('The evidence upload failed. Please try the file again.', response.status)
  return api('/evidence/complete', { id: intent.id })
}
