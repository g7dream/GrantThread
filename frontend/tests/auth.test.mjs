import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

const compile = source => ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
const moduleUrl = source => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
const apiSource = compile(await readFile(new URL('../src/api.ts', import.meta.url), 'utf8')).replace('import.meta.env.VITE_API_URL', 'undefined')
const domain = 'https://fixture.auth.eu-north-1.amazoncognito.com'
const callback = 'https://grantthread.example/grantthread/'
const authSource = compile(await readFile(new URL('../src/auth.ts', import.meta.url), 'utf8'))
  .replace(/from ['"]\.\/api['"]/, `from '${moduleUrl(apiSource)}'`)
  .replaceAll('import.meta.env.VITE_COGNITO_DOMAIN', JSON.stringify(domain))
  .replaceAll('import.meta.env.VITE_COGNITO_CLIENT_ID', JSON.stringify('fixture-client'))
  .replaceAll('import.meta.env.VITE_COGNITO_REDIRECT_URI', JSON.stringify(callback))
let moduleId = 0
const loadAuth = () => import(`${moduleUrl(authSource)}#${++moduleId}`)

function browser(t, deadline = 20000) {
  const previous = new Map(['location', 'history', 'sessionStorage', 'window'].map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]))
  const values = new Map()
  const timers = new Set()
  const result = { assigned: null, replaced: null, values, timers }
  Object.defineProperty(globalThis, 'window', { configurable: true, writable: true, value: { setTimeout: (callback, delay) => { assert.equal(delay, 20000); const timer = setTimeout(callback, deadline); timers.add(timer); return timer }, clearTimeout: timer => { clearTimeout(timer); timers.delete(timer) } } })
  Object.defineProperty(globalThis, 'location', { configurable: true, writable: true, value: { origin: 'https://grantthread.example', pathname: '/grantthread/', search: '', assign: url => { result.assigned = url } } })
  Object.defineProperty(globalThis, 'history', { configurable: true, writable: true, value: { replaceState: (_state, _title, path) => { result.replaced = path } } })
  Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, writable: true, value: { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) } })
  t.after(() => { for (const timer of timers) clearTimeout(timer); for (const [key, descriptor] of previous) { if (descriptor) Object.defineProperty(globalThis, key, descriptor); else delete globalThis[key] } })
  return result
}

for (const action of ['signin', 'signup']) {
  test(`${action} uses the intended Cognito page with a matching S256 PKCE challenge`, async t => {
    const state = browser(t)
    const auth = await loadAuth()
    await auth.signInCloud(action)
    const url = new URL(state.assigned)
    const saved = JSON.parse(state.values.get('grantthread.pkce'))
    assert.equal(url.origin, domain)
    assert.equal(url.pathname, action === 'signup' ? '/signup' : '/oauth2/authorize')
    assert.equal(url.searchParams.get('response_type'), 'code')
    assert.equal(url.searchParams.get('client_id'), 'fixture-client')
    assert.equal(url.searchParams.get('redirect_uri'), callback)
    assert.equal(url.searchParams.get('scope'), 'openid email profile grantthread/access')
    assert.equal(url.searchParams.get('code_challenge_method'), 'S256')
    assert.equal(url.searchParams.get('state'), saved.state)
    assert.match(saved.verifier, /^[A-Za-z0-9_-]{64}$/)
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(saved.verifier))
    assert.equal(url.searchParams.get('code_challenge'), Buffer.from(digest).toString('base64url'))
    assert.equal(url.searchParams.has('code_verifier'), false)
    assert.equal(url.searchParams.has('identity_provider'), false)
  })
}

test('signup callback exchanges its verifier once and clears previous demo role state', async t => {
  const state = browser(t)
  const auth = await loadAuth()
  await auth.signInCloud('signup')
  const saved = JSON.parse(state.values.get('grantthread.pkce'))
  state.values.set('grantthread.session', 'previous-token')
  state.values.set('grantthread.demo.enabled', '1')
  state.values.set('grantthread.demo.role', 'funder')
  location.search = `?code=fixture-code&state=${saved.state}`
  let calls = 0
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls++
    assert.equal(url, `${domain}/oauth2/token`)
    assert.equal(options.method, 'POST')
    assert.equal(options.body.get('code_verifier'), saved.verifier)
    assert.equal(options.body.get('redirect_uri'), callback)
    assert.equal(options.body.get('code'), 'fixture-code')
    assert.equal(options.headers.Authorization, undefined)
    assert.equal(options.headers['x-grantthread-demo-role'], undefined)
    return Response.json({ access_token: 'new-token' })
  })
  await Promise.all([auth.completeCloudSignIn(), auth.completeCloudSignIn()])
  assert.equal(calls, 1)
  assert.equal(state.values.get('grantthread.session'), 'new-token')
  assert.equal(state.values.has('grantthread.pkce'), false)
  assert.equal(state.values.has('grantthread.demo.enabled'), false)
  assert.equal(state.values.has('grantthread.demo.role'), false)
  assert.equal(state.replaced, '/grantthread/')
  assert.equal(state.timers.size, 0)
})

test('missing mismatched expired or malformed PKCE state cannot exchange a code', async t => {
  const state = browser(t)
  const valid = { state: 's'.repeat(43), verifier: 'v'.repeat(64), createdAt: Date.now() }
  const cases = [undefined, '{invalid', 'null', JSON.stringify({ ...valid, state: 'different'.repeat(5) }), JSON.stringify({ ...valid, createdAt: Date.now() - 600001 }), JSON.stringify({ ...valid, createdAt: Date.now() + 60000 }), JSON.stringify({ ...valid, verifier: '' }), JSON.stringify({ state: valid.state, verifier: valid.verifier })]
  let calls = 0
  t.mock.method(globalThis, 'fetch', async () => { calls++; return Response.json({ access_token: 'must-not-exist' }) })
  for (const stored of cases) {
    state.values.clear()
    if (stored !== undefined) state.values.set('grantthread.pkce', stored)
    location.search = `?code=fixture-code&state=${valid.state}`
    await assert.rejects((await loadAuth()).completeCloudSignIn(), /sign-in.*(expired|verification failed)/i)
    assert.equal(state.values.has('grantthread.session'), false)
    assert.equal(state.values.has('grantthread.pkce'), false)
  }
  assert.equal(calls, 0)
})

test('failed token exchange does not establish a session', async t => {
  const state = browser(t)
  const auth = await loadAuth()
  await auth.signInCloud('signup')
  const saved = JSON.parse(state.values.get('grantthread.pkce'))
  location.search = `?code=fixture-code&state=${saved.state}`
  t.mock.method(globalThis, 'fetch', async () => Response.json({ error: 'invalid_grant' }, { status: 400 }))
  await assert.rejects(auth.completeCloudSignIn(), /could not be established/)
  assert.equal(state.values.has('grantthread.session'), false)
})

test('cloud sign-out clears the token and demo role before redirecting', async t => {
  const state = browser(t)
  const auth = await loadAuth()
  state.values.set('grantthread.session', 'visitor')
  state.values.set('grantthread.demo.enabled', '1')
  state.values.set('grantthread.demo.role', 'funder')
  auth.signOutCloud()
  assert.equal(state.values.size, 0)
  const url = new URL(state.assigned)
  assert.equal(url.pathname, '/logout')
  assert.equal(url.searchParams.get('logout_uri'), callback)
})

for (const stage of ['headers', 'body']) {
  test(`secure token exchange deadline includes stalled ${stage}`, { timeout: 1000 }, async t => {
    const state = browser(t, 15)
    const auth = await loadAuth()
    await auth.signInCloud('signup')
    const saved = JSON.parse(state.values.get('grantthread.pkce'))
    location.search = `?code=fixture-code&state=${saved.state}`
    let calls = 0
    t.mock.method(globalThis, 'fetch', async (_url, options) => {
      calls++
      if (stage === 'headers') return new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true }))
      return new Response(new ReadableStream({ start(controller) { options.signal.addEventListener('abort', () => controller.error(new DOMException('Aborted', 'AbortError')), { once: true }) } }), { headers: { 'Content-Type': 'application/json' } })
    })
    await assert.rejects(auth.completeCloudSignIn(), /took too long/)
    assert.equal(calls, 1)
    assert.equal(state.values.has('grantthread.session'), false)
    assert.equal(state.timers.size, 0)
  })
}

test('a non-string access token is never stored as a session', async t => {
  const state = browser(t)
  const auth = await loadAuth()
  await auth.signInCloud('signup')
  const saved = JSON.parse(state.values.get('grantthread.pkce'))
  location.search = `?code=fixture-code&state=${saved.state}`
  t.mock.method(globalThis, 'fetch', async () => Response.json({ access_token: { invalid: true } }))
  await assert.rejects(auth.completeCloudSignIn(), /could not be established/)
  assert.equal(state.values.has('grantthread.session'), false)
  assert.equal(state.timers.size, 0)
})
