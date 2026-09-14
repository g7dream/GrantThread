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
async function request<T>(path: string, options: RequestInit, read: (response: Response, signal: AbortSignal) => Promise<T>) {
  // Bound read requests without automatically retrying financial writes.
  const readOnly = !options.method || options.method.toUpperCase() === 'GET'
  const controller = new AbortController()
  const deadline = Date.now() + 20000
  let timedOut = false
  const timeout = readOnly ? window.setTimeout(() => { timedOut = true; controller.abort() }, 20000) : undefined
  const cancel = () => controller.abort(options.signal?.reason)
  if (options.signal?.aborted) cancel()
  else options.signal?.addEventListener('abort', cancel, { once: true })
  const sessionToken = token()
  const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}), ...options.headers }
  try {
    let response: Response
    for (let attempt = 0; ; attempt++) {
      response = await fetch(apiUrl(path), { ...options, signal: controller.signal, headers })
      if (!readOnly || ![429, 503].includes(response.status) || attempt >= 2) break
      const retryAfter = response.headers.get('Retry-After')?.trim()
      const serverDelay = retryAfter ? /^\d+(?:\.\d+)?$/.test(retryAfter) ? Number(retryAfter) * 1000 : Math.max(0, Date.parse(retryAfter) - Date.now()) : 0
      const delay = Math.max(500 * 2 ** attempt + Math.floor(Math.random() * 250), Number.isNaN(serverDelay) ? 0 : serverDelay)
      if (delay >= deadline - Date.now()) break
      // Release this response and retry only safe reads, within the original deadline.
      void response.body?.cancel().catch(() => {})
      await new Promise<void>((resolve, reject) => {
        let timer: number | undefined
        const finish = (aborted = false) => {
          window.clearTimeout(timer)
          controller.signal.removeEventListener('abort', abort)
          if (aborted) reject(controller.signal.reason || new DOMException('Aborted', 'AbortError'))
          else resolve()
        }
        const abort = () => finish(true)
        if (controller.signal.aborted) { abort(); return }
        controller.signal.addEventListener('abort', abort, { once: true })
        timer = window.setTimeout(() => finish(), delay)
      })
    }
    if (!response.ok) {
      if (response.status === 401 && path !== '/demo/login') window.dispatchEvent(new Event('grantthread:unauthorized'))
      const payload = await response.json().catch(error => { if (controller.signal.aborted) throw error; return {} })
      const body = payload && typeof payload === 'object' ? payload : {}
      const fallback = [429, 503].includes(response.status) ? 'The workspace server is busy. Please try again shortly.' : `Request failed (${response.status}). Please try again.`
      throw new ApiError(typeof body.error === 'string' ? body.error : typeof body.detail === 'string' ? body.detail : fallback, response.status, body.code)
    }
    // Keep the deadline active until JSON or download bytes finish arriving.
    return await read(response, controller.signal)
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
function sourceDownload(value: unknown): { downloadUrl: string; filename: string; contentType: string } {
  const invalid = () => new ApiError('The server returned an invalid source download link. Please reopen the source and try again.', 0, 'invalid_download')
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw invalid()
  const item = value as Record<string, unknown>
  if (typeof item.downloadUrl !== 'string' || item.downloadUrl.length > 8192 || /[\x00-\x20\\]/.test(item.downloadUrl)
    || typeof item.filename !== 'string' || !item.filename || item.filename.length > 240 || /[\x00-\x1f\x7f<>:"/\\|?*]/.test(item.filename)
    || typeof item.contentType !== 'string' || item.contentType.length > 255 || !/^[\w!#$&^.+-]+\/[\w!#$&^.+-]+(?:;[^\r\n]*)?$/.test(item.contentType)) throw invalid()
  let target: URL
  try { target = new URL(item.downloadUrl) } catch { throw invalid() }
  // Only the already-authorised API may supply a signed S3 object destination.
  // No app token or cookie is ever forwarded to this separate origin.
  if (target.protocol !== 'https:' || target.username || target.password || target.port || target.hash || target.pathname === '/'
    || !/^(?:[a-z0-9][a-z0-9.-]*\.)?s3(?:[.-][a-z0-9-]+)?\.amazonaws\.com$/.test(target.hostname)) throw invalid()
  const query = target.searchParams
  const signedV4 = query.get('X-Amz-Algorithm') === 'AWS4-HMAC-SHA256' && !!query.get('X-Amz-Credential')
    && /^\d{8}T\d{6}Z$/.test(query.get('X-Amz-Date') || '') && /^[1-9]\d*$/.test(query.get('X-Amz-Expires') || '')
    && /^[a-fA-F0-9]{64}$/.test(query.get('X-Amz-Signature') || '') && query.get('X-Amz-SignedHeaders') === 'host'
  const signedV2 = !!query.get('AWSAccessKeyId') && !!query.get('Signature') && /^[1-9]\d*$/.test(query.get('Expires') || '')
  if (!signedV4 && !signedV2) throw invalid()
  return { downloadUrl: item.downloadUrl, filename: item.filename, contentType: item.contentType }
}
export async function download(path: string, name: string) {
  const result = await request(path, { redirect: 'error' }, async (response, signal) => {
    const original = await response.blob()
    if (!response.headers.get('Content-Type')?.toLowerCase().includes('application/json')) return { blob: original, name }
    let payload: unknown
    try { payload = JSON.parse(await original.text()) } catch { throw new ApiError('The server returned an invalid download response.', response.status, 'invalid_download') }
    // Report manifests are ordinary JSON files, not signed-source descriptors.
    if (!payload || typeof payload !== 'object' || !('downloadUrl' in payload)) return { blob: original, name }
    const source = sourceDownload(payload)
    const file = await fetch(source.downloadUrl, { method: 'GET', credentials: 'omit', redirect: 'error', referrerPolicy: 'no-referrer', signal })
    if (!file.ok) {
      void file.body?.cancel().catch(() => {})
      throw new ApiError('The source file could not be downloaded. Reopen it and try again.', file.status, 'source_download')
    }
    return { blob: new Blob([await file.blob()], { type: source.contentType }), name: source.filename }
  })
  const blob = result.blob
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url; link.download = result.name; link.click()
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
