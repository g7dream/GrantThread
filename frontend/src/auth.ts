import { setToken } from './api'
const domain = (import.meta.env.VITE_COGNITO_DOMAIN || '').replace(/\/$/, '')
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID || ''
const redirectUri = import.meta.env.VITE_COGNITO_REDIRECT_URI || `${location.origin}${location.pathname}`
export const cloudConfigured = Boolean(domain && clientId)
function base64Url(bytes: Uint8Array) { return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') }
export async function signInCloud(action: 'signin' | 'signup' = 'signin') {
  if (!cloudConfigured) throw new Error('Secure sign-in is not configured for this website.')
  const verifier = base64Url(crypto.getRandomValues(new Uint8Array(48)))
  const state = base64Url(crypto.getRandomValues(new Uint8Array(32)))
  const challenge = base64Url(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))))
  sessionStorage.setItem('grantthread.pkce', JSON.stringify({ verifier, state, createdAt: Date.now() }))
  const params = new URLSearchParams({ response_type: 'code', client_id: clientId, redirect_uri: redirectUri, scope: 'openid email profile grantthread/access', state, code_challenge: challenge, code_challenge_method: 'S256' })
  location.assign(`${domain}${action === 'signup' ? '/signup' : '/oauth2/authorize'}?${params}`)
}
let callbackPromise: Promise<void> | undefined
export function completeCloudSignIn() {
  if (callbackPromise) return callbackPromise
  callbackPromise = (async () => {
    const params = new URLSearchParams(location.search)
    if (params.has('error')) { sessionStorage.removeItem('grantthread.pkce'); history.replaceState(null, '', location.pathname); throw new Error(params.get('error_description') || 'Sign-in could not be completed.') }
    const code = params.get('code')
    if (!code) return
    const stored = sessionStorage.getItem('grantthread.pkce')
    sessionStorage.removeItem('grantthread.pkce')
    history.replaceState(null, '', location.pathname)
    if (!stored) throw new Error('This sign-in session expired. Please sign in again.')
    let saved: { verifier?: unknown; state?: unknown; createdAt?: unknown }
    try { saved = JSON.parse(stored) } catch { throw new Error('Sign-in verification failed. Please sign in again.') }
    const { verifier, state, createdAt } = saved || {}
    if (typeof verifier !== 'string' || !/^[A-Za-z0-9_-]{43,128}$/.test(verifier) || typeof state !== 'string' || !/^[A-Za-z0-9_-]{32,128}$/.test(state)
      || typeof createdAt !== 'number' || !Number.isFinite(createdAt) || createdAt > Date.now() || Date.now() - createdAt > 600000
      || params.get('state') !== state) throw new Error('Sign-in verification failed. Please sign in again.')
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), 20000)
    try {
      const response = await fetch(`${domain}/oauth2/token`, { method: 'POST', signal: controller.signal, headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ grant_type: 'authorization_code', client_id: clientId, code, redirect_uri: redirectUri, code_verifier: verifier }) })
      const data = await response.json()
      if (!response.ok || typeof data?.access_token !== 'string' || !data.access_token) throw new Error('The secure session could not be established. Please sign in again.')
      setToken(data.access_token)
    } catch (failure) {
      if (controller.signal.aborted) throw new Error('Secure sign-in took too long to respond. Please sign in again.')
      throw failure
    } finally { window.clearTimeout(timer) }
  })()
  return callbackPromise
}
export function signOutCloud() {
  setToken(null)
  if (cloudConfigured) location.assign(`${domain}/logout?${new URLSearchParams({ client_id: clientId, logout_uri: redirectUri })}`)
}
