import { setToken } from './api'
const domain = (import.meta.env.VITE_COGNITO_DOMAIN || '').replace(/\/$/, '')
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID || ''
const redirectUri = import.meta.env.VITE_COGNITO_REDIRECT_URI || `${location.origin}${location.pathname}`
export const cloudConfigured = Boolean(domain && clientId)
function base64Url(bytes: Uint8Array) { return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') }
export async function signInCloud() {
  const verifier = base64Url(crypto.getRandomValues(new Uint8Array(48)))
  const state = base64Url(crypto.getRandomValues(new Uint8Array(32)))
  const challenge = base64Url(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))))
  sessionStorage.setItem('grantthread.pkce', JSON.stringify({ verifier, state, createdAt: Date.now() }))
  const params = new URLSearchParams({ response_type: 'code', client_id: clientId, redirect_uri: redirectUri, scope: 'openid email profile grantthread/access', state, code_challenge: challenge, code_challenge_method: 'S256' })
  location.assign(`${domain}/oauth2/authorize?${params}`)
}
let callbackPromise: Promise<void> | undefined
export function completeCloudSignIn() {
  if (callbackPromise) return callbackPromise
  callbackPromise = (async () => {
    const params = new URLSearchParams(location.search)
    if (params.has('error')) { history.replaceState(null, '', location.pathname); throw new Error(params.get('error_description') || 'Sign-in could not be completed.') }
    const code = params.get('code')
    if (!code) return
    const stored = sessionStorage.getItem('grantthread.pkce')
    sessionStorage.removeItem('grantthread.pkce')
    history.replaceState(null, '', location.pathname)
    if (!stored) throw new Error('This sign-in session expired. Please sign in again.')
    const { verifier, state, createdAt } = JSON.parse(stored)
    if (params.get('state') !== state || Date.now() - createdAt > 600000) throw new Error('Sign-in verification failed. Please sign in again.')
    const response = await fetch(`${domain}/oauth2/token`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ grant_type: 'authorization_code', client_id: clientId, code, redirect_uri: redirectUri, code_verifier: verifier }) })
    const data = await response.json()
    if (!response.ok || !data.access_token) throw new Error('The secure session could not be established. Please sign in again.')
    setToken(data.access_token)
  })()
  return callbackPromise
}
export function signOutCloud() {
  setToken(null)
  if (cloudConfigured) location.assign(`${domain}/logout?${new URLSearchParams({ client_id: clientId, logout_uri: redirectUri })}`)
}
