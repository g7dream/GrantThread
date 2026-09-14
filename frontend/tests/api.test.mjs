import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

// Vite replaces this public build setting. Compile the real module with its
// default /api value so the Node tests exercise the browser request lifecycle.
const source = await readFile(new URL('../src/api.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText.replace('import.meta.env.VITE_API_URL', 'undefined')
const { api, download } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`)

function browser(t, fetcher) {
  const previousWindow = globalThis.window
  const previousStorage = globalThis.sessionStorage
  const browserWindow = new EventTarget()
  const timers = new Set()
  let started = 0
  browserWindow.setTimeout = callback => {
    started++
    const timer = setTimeout(callback, 15)
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
  return { window: browserWindow, pending: () => timers.size, started: () => started }
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
  await new Promise(resolve => setTimeout(resolve, 25))
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
