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
async function request<T>(path: string, options: RequestInit, read: (response: Response) => Promise<T>) {
  // Bound read requests without automatically retrying financial writes.
  const controller = new AbortController()
  let timedOut = false
  const timeout = options.method && options.method !== 'GET' ? undefined : window.setTimeout(() => { timedOut = true; controller.abort() }, 20000)
  const cancel = () => controller.abort(options.signal?.reason)
  if (options.signal?.aborted) cancel()
  else options.signal?.addEventListener('abort', cancel, { once: true })
  try {
    const response = await fetch(apiUrl(path), { ...options, signal: controller.signal, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(token() ? { Authorization: `Bearer ${token()}` } : {}), ...options.headers } })
    if (!response.ok) {
      if (response.status === 401 && path !== '/demo/login') window.dispatchEvent(new Event('grantthread:unauthorized'))
      const payload = await response.json().catch(error => { if (controller.signal.aborted) throw error; return {} })
      const body = payload && typeof payload === 'object' ? payload : {}
      throw new ApiError(typeof body.error === 'string' ? body.error : typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}). Please try again.`, response.status, body.code)
    }
    // Keep the deadline active until JSON or download bytes finish arriving.
    return await read(response)
  } catch (error) {
    if (timedOut) throw new ApiError('The workspace server took too long to respond. Check your connection and try again.', 0, 'timeout')
    if (error instanceof TypeError) throw new ApiError(options.method && options.method !== 'GET' ? 'The server connection was interrupted. Check whether your change was saved before trying again.' : 'The workspace server could not be reached. Check your connection and try again.', 0, 'network')
    throw error
  } finally {
    window.clearTimeout(timeout)
    options.signal?.removeEventListener('abort', cancel)
  }
}
export async function api<T>(path: string, body?: unknown): Promise<T> {
  return request(path, body === undefined ? {} : { method: 'POST', body: JSON.stringify(body) }, async response => {
    if (response.status === 204) return undefined as T
    if (!response.headers.get('Content-Type')?.toLowerCase().includes('application/json')) throw new ApiError('The workspace server returned a web page instead of data. Its API connection needs to be checked.', response.status, 'invalid_response')
    return response.json()
  })
}
export async function download(path: string, name: string) {
  const blob = await request(path, {}, response => response.blob())
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
