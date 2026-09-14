import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

// Vite replaces this public build setting. Compile the real module with its
// default /api value so the Node tests exercise the browser request lifecycle.
const source = await readFile(new URL('../src/api.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText.replace('import.meta.env.VITE_API_URL', 'undefined')
const { api, download, uploadEvidence, demoRole, setDemoRole, setDemoEnabled, setToken } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`)

function storedSession() {
  const values = new Map()
  globalThis.sessionStorage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) }
  return values
}

function browser(t, fetcher, delayFor = delay => delay === 20000 ? 100 : 1) {
  const previousWindow = globalThis.window
  const previousStorage = globalThis.sessionStorage
  const browserWindow = new EventTarget()
  const timers = new Set()
  let started = 0
  const delays = []
  browserWindow.setTimeout = (callback, delay) => {
    started++
    delays.push(delay)
    const timer = setTimeout(callback, delayFor(delay))
    timers.add(timer)
    return timer
  }
  browserWindow.clearTimeout = timer => { clearTimeout(timer); timers.delete(timer) }
  globalThis.window = browserWindow
  globalThis.sessionStorage = { getItem: () => null }
  t.mock.method(globalThis, 'fetch', fetcher)
  t.after(() => {
    for (const timer of timers) clearTimeout(timer)
    if (previousWindow === undefined) delete globalThis.window
    else globalThis.window = previousWindow
    if (previousStorage === undefined) delete globalThis.sessionStorage
    else globalThis.sessionStorage = previousStorage
  })
  return { window: browserWindow, pending: () => timers.size, started: () => started, delays }
}

function stalledBody(signal, status = 200, contentType = 'application/json') {
  const stream = new ReadableStream({ start(controller) {
    signal.addEventListener('abort', () => controller.error(new DOMException('Aborted', 'AbortError')), { once: true })
  } })
  return new Response(stream, { status, headers: { 'Content-Type': contentType } })
}

test('read deadline covers a request that never returns headers', { timeout: 1000 }, async t => {
  const state = browser(t, (_url, options) => new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })))
  await assert.rejects(api('/health'), error => error.code === 'timeout' && error.status === 0)
  assert.equal(state.pending(), 0)
})

test('read deadline stays active after JSON response headers arrive', { timeout: 1000 }, async t => {
  const state = browser(t, async (_url, options) => stalledBody(options.signal))
  await assert.rejects(api('/health'), error => error.code === 'timeout')
  assert.equal(state.pending(), 0)
})

test('read deadline covers an HTTP error body without disguising the timeout', { timeout: 1000 }, async t => {
  const state = browser(t, async (_url, options) => stalledBody(options.signal, 503))
  await assert.rejects(api('/financials'), error => error.code === 'timeout')
  assert.equal(state.pending(), 0)
})

test('download deadline includes the file body', { timeout: 1000 }, async t => {
  const state = browser(t, async (_url, options) => stalledBody(options.signal, 200, 'application/octet-stream'))
  await assert.rejects(download('/activity/csv', 'history.csv'), error => error.code === 'timeout')
  assert.equal(state.pending(), 0)
})

test('completed JSON clears its deadline and does not abort later', { timeout: 1000 }, async t => {
  let signal
  const state = browser(t, async (_url, options) => {
    signal = options.signal
    return Response.json({ status: 'ok', mode: 'local' })
  })
  assert.deepEqual(await api('/health'), { status: 'ok', mode: 'local' })
  assert.equal(state.pending(), 0)
  await new Promise(resolve => setTimeout(resolve, 120))
  assert.equal(signal.aborted, false)
})

test('failed financial writes are not retried or assigned a read timeout', { timeout: 1000 }, async t => {
  let calls = 0
  const state = browser(t, async (_url, options) => {
    calls++
    assert.equal(options.method, 'POST')
    throw new TypeError('Connection interrupted')
  })
  await assert.rejects(api('/financials/receipts', { sourceAmount: '25.00' }), error => error.code === 'network' && error.message.includes('Check whether your change was saved'))
  assert.equal(calls, 1)
  assert.equal(state.started(), 0)
})

test('an HTML page at the API address is not treated as workspace data', { timeout: 1000 }, async t => {
  const state = browser(t, async () => new Response('<html>Website preview</html>', { headers: { 'Content-Type': 'text/html' } }))
  await assert.rejects(api('/health'), error => error.code === 'invalid_response')
  assert.equal(state.pending(), 0)
})

test('expired sessions are reported even when the error body stalls', { timeout: 1000 }, async t => {
  const state = browser(t, async (_url, options) => stalledBody(options.signal, 401))
  let expired = 0
  state.window.addEventListener('grantthread:unauthorized', () => { expired++ })
  await assert.rejects(api('/session'), error => error.code === 'timeout')
  assert.equal(expired, 1)
})

test('a throttled GET retries within one deadline and returns recovered data', { timeout: 1000 }, async t => {
  let calls = 0
  const signals = []
  const state = browser(t, async (_url, options) => {
    signals.push(options.signal)
    return ++calls === 1 ? Response.json({ message: 'Too Many Requests' }, { status: 429 }) : Response.json({ events: [] })
  })
  assert.deepEqual(await api('/activity'), { events: [] })
  assert.equal(calls, 2)
  assert.equal(signals[0], signals[1])
  assert.equal(state.delays.filter(delay => delay === 20000).length, 1)
  assert.equal(state.pending(), 0)
})

test('temporarily unavailable reads honor Retry-After before recovery', { timeout: 1000 }, async t => {
  let calls = 0
  const state = browser(t, async () => ++calls === 1 ? Response.json({}, { status: 503, headers: { 'Retry-After': '2' } }) : Response.json({ ready: true }))
  assert.deepEqual(await api('/financials'), { ready: true })
  assert.equal(calls, 2)
  assert.equal(state.delays[1], 2000)
})

test('persistent throttling stops after two retries with a useful error', { timeout: 1000 }, async t => {
  let calls = 0
  const state = browser(t, async () => { calls++; return Response.json({}, { status: 429 }) })
  await assert.rejects(api('/portfolio'), error => error.status === 429 && error.message.includes('busy'))
  assert.equal(calls, 3)
  assert.equal(state.delays.filter(delay => delay === 20000).length, 1)
  assert.equal(state.pending(), 0)
})

test('a Retry-After beyond the deadline does not cause an early retry', { timeout: 1000 }, async t => {
  let calls = 0
  const state = browser(t, async () => { calls++; return Response.json({}, { status: 429, headers: { 'Retry-After': '30' } }) })
  await assert.rejects(api('/health'), error => error.status === 429)
  assert.equal(calls, 1)
  assert.deepEqual(state.delays, [20000])
})

test('the total deadline interrupts backoff without another request', { timeout: 1000 }, async t => {
  let calls = 0
  const state = browser(t, async () => { calls++; return Response.json({}, { status: 503 }) }, delay => delay === 20000 ? 5 : 40)
  await assert.rejects(api('/health'), error => error.code === 'timeout')
  assert.equal(calls, 1)
  assert.equal(state.pending(), 0)
})

for (const status of [429, 503]) {
  test(`financial writes never retry HTTP ${status}`, { timeout: 1000 }, async t => {
    let calls = 0
    const state = browser(t, async () => { calls++; return Response.json({}, { status }) })
    await assert.rejects(api('/financials/receipts', { sourceAmount: '25.00' }), error => error.status === status)
    assert.equal(calls, 1)
    assert.equal(state.started(), 0)
  })
}

test('ordinary server failures are not automatically retried', { timeout: 1000 }, async t => {
  let calls = 0
  browser(t, async () => { calls++; return Response.json({}, { status: 500 }) })
  await assert.rejects(api('/portfolio'), error => error.status === 500)
  assert.equal(calls, 1)
})

const signedSource = 'https://fixture-bucket.s3.eu-north-1.amazonaws.com/source.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=fixture&X-Amz-Date=20260914T180000Z&X-Amz-Expires=300&X-Amz-SignedHeaders=host&X-Amz-Signature=' + 'a'.repeat(64)
const sourceDescriptor = downloadUrl => ({ downloadUrl, filename: 'Source document.pdf', contentType: 'application/pdf' })

function downloadDom(t) {
  const previous = globalThis.document
  const saved = { blob: null, name: null, clicks: 0 }
  globalThis.document = { createElement(tag) {
    assert.equal(tag, 'a')
    return { click() { saved.name = this.download; saved.clicks++ } }
  } }
  t.mock.method(URL, 'createObjectURL', blob => { saved.blob = blob; return 'blob:download-fixture' })
  // Browser cleanup remains scheduled, without keeping the Node test process alive.
  const schedule = globalThis.setTimeout
  t.mock.method(globalThis, 'setTimeout', (callback, delay, ...args) => {
    const timer = schedule(callback, delay, ...args)
    if (delay === 10000) timer.unref()
    return timer
  })
  t.after(() => { if (previous === undefined) delete globalThis.document; else globalThis.document = previous })
  return saved
}

test('signed source uses a separate credentialless GET within the API read deadline', { timeout: 1000 }, async t => {
  const calls = []
  const state = browser(t, async (url, options) => {
    calls.push({ url, options })
    return calls.length === 1 ? Response.json(sourceDescriptor(signedSource)) : new Response('fictional PDF bytes')
  })
  storedSession()
  setToken('fictional-session-token'); setDemoEnabled(true); setDemoRole('funder')
  const saved = downloadDom(t)
  await download('/evidence/fixture/download', 'old-fallback-name')
  assert.equal(calls[0].url, '/api/evidence/fixture/download')
  assert.equal(calls[0].options.headers.Authorization, 'Bearer fictional-session-token')
  assert.equal(calls[0].options.headers['x-grantthread-demo-role'], 'funder')
  assert.equal(calls[0].options.redirect, 'error')
  assert.equal(calls[1].url, signedSource)
  assert.equal(calls[1].options.method, 'GET')
  assert.equal(calls[1].options.credentials, 'omit')
  assert.equal(calls[1].options.redirect, 'error')
  assert.equal(calls[1].options.referrerPolicy, 'no-referrer')
  assert.equal(calls[1].options.headers, undefined)
  assert.equal(calls[1].options.signal, calls[0].options.signal)
  assert.deepEqual(state.delays, [20000])
  assert.equal(state.pending(), 0)
  assert.equal(saved.clicks, 1)
  assert.equal(saved.name, 'Source document.pdf')
  assert.equal(saved.blob.type, 'application/pdf')
  assert.equal(await saved.blob.text(), 'fictional PDF bytes')
})

test('global S3 SigV4 and legacy descriptors are supported without app credentials', { timeout: 1000 }, async t => {
  const urls = [signedSource.replace('.s3.eu-north-1.', '.s3.'), 'https://fixture-bucket.s3.amazonaws.com/source.pdf?AWSAccessKeyId=fixture&Signature=fixture&Expires=1790000000']
  let url
  let calls = 0
  browser(t, async (target, options) => {
    if (++calls % 2 === 1) return Response.json(sourceDescriptor(url))
    assert.equal(target, url)
    assert.equal(options.credentials, 'omit')
    assert.equal(options.headers, undefined)
    return new Response('source')
  })
  const saved = downloadDom(t)
  for (url of urls) await download('/shared-reports/fixture/attachments/source', 'fallback')
  assert.equal(calls, 4)
  assert.equal(saved.clicks, 2)
})

test('unsafe or unsigned descriptor destinations are rejected before any object request', { timeout: 1000 }, async t => {
  let target
  let calls = 0
  browser(t, async url => {
    calls++
    assert.equal(url, '/api/evidence/fixture/download')
    return Response.json(sourceDescriptor(target))
  })
  const invalid = [
    'javascript:alert(1)', 'http://fixture-bucket.s3.amazonaws.com/source.pdf',
    'https://127.0.0.1/source', 'https://example.com/source',
    signedSource.replace('fixture-bucket.s3.eu-north-1.amazonaws.com', 'fixture-bucket.s3.eu-north-1.amazonaws.com.example.com'),
    signedSource.replace('https://', 'https://user:password@'),
    signedSource.replace('.com/', '.com:8443/'), signedSource + '#fragment',
    signedSource.replace('source.pdf?', 'source.pdf?X-Amz-Signature=invalid&ignored='),
    'https://fixture-bucket.s3.amazonaws.com/source.pdf',
    signedSource.replace('https://', 'https:\\'), signedSource.replace('https://', 'https:\t//'),
  ]
  for (target of invalid) await assert.rejects(download('/evidence/fixture/download', 'source'), error => error.code === 'invalid_download')
  assert.equal(calls, invalid.length)
})

test('invalid descriptor filenames and types never cause an object request', { timeout: 1000 }, async t => {
  let descriptor
  let calls = 0
  browser(t, async () => { calls++; return Response.json(descriptor) })
  const invalid = [
    { ...sourceDescriptor(signedSource), filename: '../source.pdf' },
    { ...sourceDescriptor(signedSource), filename: 'source\n.pdf' },
    { ...sourceDescriptor(signedSource), filename: '' },
    { ...sourceDescriptor(signedSource), contentType: 'text/plain\r\nx-invalid: true' },
    { ...sourceDescriptor(signedSource), downloadUrl: null },
  ]
  for (descriptor of invalid) await assert.rejects(download('/evidence/fixture/download', 'source'), error => error.code === 'invalid_download')
  assert.equal(calls, invalid.length)
})

test('ordinary JSON manifests remain exact inline downloads', { timeout: 1000 }, async t => {
  const text = '{\n  "attachments": [], "version": 1\n}\n'
  let calls = 0
  browser(t, async () => { calls++; return new Response(text, { headers: { 'Content-Type': 'application/json' } }) })
  const saved = downloadDom(t)
  await download('/reports/fixture/manifest', 'manifest.json')
  assert.equal(calls, 1)
  assert.equal(saved.name, 'manifest.json')
  assert.equal(await saved.blob.text(), text)
})

test('inline PDF XLSX and local source bytes retain their original download behavior', { timeout: 1000 }, async t => {
  const bytes = Uint8Array.from([0, 80, 75, 255, 10])
  let type
  let calls = 0
  browser(t, async () => { calls++; return new Response(bytes, { headers: { 'Content-Type': type } }) })
  const saved = downloadDom(t)
  for (type of ['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/plain']) {
    await download('/local-file', 'caller-name')
    assert.equal(saved.name, 'caller-name')
    assert.equal(saved.blob.type, type)
    assert.deepEqual(new Uint8Array(await saved.blob.arrayBuffer()), bytes)
  }
  assert.equal(calls, 3)
  assert.equal(saved.clicks, 3)
})

test('signed source deadline covers stalled object response headers', { timeout: 1000 }, async t => {
  let calls = 0
  const state = browser(t, (_url, options) => ++calls === 1 ? Promise.resolve(Response.json(sourceDescriptor(signedSource))) : new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })))
  await assert.rejects(download('/evidence/fixture/download', 'source'), error => error.code === 'timeout')
  assert.equal(calls, 2)
  assert.deepEqual(state.delays, [20000])
  assert.equal(state.pending(), 0)
})

test('signed source deadline covers the object body without starting another timeout', { timeout: 1000 }, async t => {
  let calls = 0
  const state = browser(t, async (_url, options) => ++calls === 1 ? Response.json(sourceDescriptor(signedSource)) : stalledBody(options.signal, 200, 'application/pdf'))
  await assert.rejects(download('/evidence/fixture/download', 'source'), error => error.code === 'timeout')
  assert.equal(calls, 2)
  assert.deepEqual(state.delays, [20000])
  assert.equal(state.pending(), 0)
})

test('an expired object link reports a source error without expiring the app session', { timeout: 1000 }, async t => {
  let calls = 0
  const state = browser(t, async () => ++calls === 1 ? Response.json(sourceDescriptor(signedSource)) : new Response('<Error>Expired</Error>', { status: 403 }))
  let expired = 0
  state.window.addEventListener('grantthread:unauthorized', () => expired++)
  await assert.rejects(download('/evidence/fixture/download', 'source'), error => error.code === 'source_download' && error.status === 403)
  assert.equal(calls, 2)
  assert.equal(expired, 0)
  assert.equal(state.pending(), 0)
})

test('demo roles require server-enabled session state and allow only grantee or funder headers', async t => {
  const headers = []
  browser(t, async (_url, options) => { headers.push(options.headers); return Response.json({}) })
  const values = storedSession()
  setDemoEnabled(true); setDemoRole('funder')
  await api('/health')
  assert.equal(headers.at(-1)['x-grantthread-demo-role'], undefined)
  setToken('visitor-one')
  setDemoRole('funder')
  await api('/session')
  assert.equal(headers.at(-1)['x-grantthread-demo-role'], undefined)
  setDemoEnabled(true); setDemoRole('grantee')
  await api('/session')
  assert.equal(headers.at(-1)['x-grantthread-demo-role'], 'grantee')
  setDemoRole('funder')
  await api('/shared-reports')
  assert.equal(headers.at(-1)['x-grantthread-demo-role'], 'funder')
  values.set('grantthread.demo.role', 'admin\r\nx-other: unsafe')
  await api('/session')
  assert.equal(headers.at(-1)['x-grantthread-demo-role'], 'grantee')
  assert.equal(demoRole(), 'grantee')
  assert.throws(() => setDemoRole('admin'), /supported demo role/)
  values.set('grantthread.demo.enabled', 'true')
  await api('/session')
  assert.equal(headers.at(-1)['x-grantthread-demo-role'], undefined)
})

test('new tokens and sign-out clear demo role preferences while the same token preserves them', async t => {
  browser(t, async () => Response.json({}))
  const values = storedSession()
  setToken('visitor-one'); setDemoEnabled(true); setDemoRole('funder')
  setToken('visitor-one')
  assert.equal(values.get('grantthread.demo.enabled'), '1')
  assert.equal(demoRole(), 'funder')
  setToken('visitor-two')
  assert.equal(values.has('grantthread.demo.enabled'), false)
  assert.equal(values.has('grantthread.demo.role'), false)
  setDemoEnabled(true); setDemoRole('funder'); setToken(null)
  assert.equal(values.has('grantthread.session'), false)
  assert.equal(values.has('grantthread.demo.enabled'), false)
  assert.equal(values.has('grantthread.demo.role'), false)
})

for (const localUpload of [false, true]) {
  test(`${localUpload ? 'API upload retains' : 'S3 upload excludes'} authenticated demo role headers`, async t => {
    const origin = 'https://grantthread.example'
    const previousLocation = globalThis.location
    globalThis.location = { origin }
    t.after(() => { if (previousLocation === undefined) delete globalThis.location; else globalThis.location = previousLocation })
    const uploadUrl = localUpload ? '/api/upload/fixture' : 'https://fixture-bucket.s3.amazonaws.com/source?signature=fixture'
    const calls = []
    browser(t, async (url, options) => {
      calls.push({ url, options })
      if (calls.length === 1) return Response.json({ id: 'fixture', uploadUrl, method: 'PUT', headers: { 'Content-Type': 'text/plain' } })
      if (calls.length === 2) return new Response(null, { status: 200 })
      return Response.json({ evidence: { id: 'fixture' } })
    })
    storedSession(); setToken('visitor'); setDemoEnabled(true); setDemoRole('grantee')
    await uploadEvidence(new File(['fictional source'], 'source.txt', { type: 'text/plain' }), { grantIds: ['fixture'] })
    assert.equal(calls.length, 3)
    for (const index of [0, 2]) {
      assert.equal(calls[index].options.headers.Authorization, 'Bearer visitor')
      assert.equal(calls[index].options.headers['x-grantthread-demo-role'], 'grantee')
    }
    assert.equal(calls[1].options.headers.Authorization, localUpload ? 'Bearer visitor' : undefined)
    assert.equal(calls[1].options.headers['x-grantthread-demo-role'], localUpload ? 'grantee' : undefined)
  })
}
