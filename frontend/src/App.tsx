import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Activity as ActivityIcon, ArrowRight, ArrowUpRight, Building2, CheckCheck, ChevronDown, CircleHelp, Clock3, FileStack, Files, History, LayoutDashboard, LogOut, Menu, Network, RefreshCw, ShieldCheck, Wallet, X } from 'lucide-react'
import { api, apiUrl, setToken, token } from './api'
import { cloudConfigured, completeCloudSignIn, signInCloud, signOutCloud } from './auth'
import { Badge, Loading, Modal, Notice } from './components'
import { PortfolioPage, GrantPage } from './Portfolio'
import { EvidencePage } from './Evidence'
import { DecisionsPage } from './Decisions'
import { ReportsPage, SharedPage, ClarificationsPage } from './Reports'
import { ResponseEstimatesPage } from './ResponseEstimates'
import { FinancialsPage } from './Financials'
import { ActivityHistoryPage } from './ActivityHistory'
import type { User } from './types'

function Logo() { return <a href="#/" className="brand" aria-label="GrantThread home"><span className="brand-mark"><Network size={23} strokeWidth={1.8} /></span><span>Grant<span className="brand-light">Thread</span></span></a> }
export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [mode, setMode] = useState('')
  const [booting, setBooting] = useState(true)
  const [connectionError, setConnectionError] = useState('')
  const [connectionAttempt, setConnectionAttempt] = useState(0)
  const [error, setError] = useState('')
  const [path, setPath] = useState(location.hash.slice(1) || '/')
  const [mobileOpen, setMobileOpen] = useState(false)
  const menuButton = useRef<HTMLButtonElement>(null)
  const pendingNavigationFocus = useRef<'menu' | 'main' | null>(null)
  const [identityOpen, setIdentityOpen] = useState(false)
  const [resetOpen, setResetOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [revision, setRevision] = useState(0)
  const refresh = () => setRevision(n => n + 1)
  function closeMobileNavigation() { pendingNavigationFocus.current = 'menu'; setMobileOpen(false) }
  useLayoutEffect(() => {
    // The workspace must no longer be inert before restoring focus into it.
    if (mobileOpen) { document.getElementById('close-mobile-navigation')?.focus(); return }
    const target = pendingNavigationFocus.current
    pendingNavigationFocus.current = null
    if (target === 'menu') menuButton.current?.focus({ preventScroll: true })
    else if (target === 'main') document.getElementById('main')?.focus({ preventScroll: true })
  }, [mobileOpen, path])
  useEffect(() => {
    if (!mobileOpen) return
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !document.querySelector('dialog[open]')) { event.preventDefault(); closeMobileNavigation() }
    }
    document.addEventListener('keydown', escape)
    return () => document.removeEventListener('keydown', escape)
  }, [mobileOpen])
  useEffect(() => {
    const change = () => { pendingNavigationFocus.current = 'main'; setPath(location.hash.slice(1) || '/'); setMobileOpen(false); window.scrollTo({ top: 0 }) }
    const unauthorized = () => { setToken(null); setUser(null); setError('Your session has expired. Please sign in again.') }
    window.addEventListener('hashchange', change); window.addEventListener('grantthread:unauthorized', unauthorized)
    return () => { window.removeEventListener('hashchange', change); window.removeEventListener('grantthread:unauthorized', unauthorized) }
  }, [])
  useEffect(() => {
    let active = true
    setBooting(true); setConnectionError(''); setMode('')
    async function boot() {
      try { await completeCloudSignIn() } catch (failure) { if (active) setError((failure as Error).message) }
      try {
        const health = await api<{ status: string; mode: string }>('/health')
        if (!active) return
        if (health.status !== 'ok' || !['local', 'aws'].includes(health.mode)) throw new Error('This address did not return a GrantThread server connection.')
        setMode(health.mode)
      } catch (failure) {
        if (active) { setConnectionError((failure as Error).message); setBooting(false) }
        return
      }
      try {
        if (token()) { const session = await api<{ user: User; mode: string }>('/session'); if (active) { setUser(session.user); setMode(session.mode) } }
      } catch (failure) { if (active) setError((failure as Error).message) }
      finally { if (active) setBooting(false) }
    }
    void boot()
    return () => { active = false }
  }, [connectionAttempt])
  async function login(identity: string) {
    setBusy(true); setError('')
    try { const result = await api<{ token: string; user: User }>('/demo/login', { identity }); setToken(result.token); setUser(result.user); setIdentityOpen(false); location.hash = '/'; refresh() } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  function logout() { setToken(null); setUser(null); setIdentityOpen(false); if (mode !== 'local') signOutCloud() }
  const local = mode === 'local'
  const funder = user?.role === 'funder'
  const nav = funder ? [{ href: '/', title: 'Funded portfolio', icon: LayoutDashboard }, { href: '/questions', title: 'Clarifications', icon: CircleHelp }] : [{ href: '/', title: 'Portfolio', icon: LayoutDashboard }, { href: '/evidence', title: 'Evidence inbox', icon: FileStack }, { href: '/decisions', title: 'Decisions', icon: CheckCheck }, { href: '/financials', title: 'Financials', icon: Wallet }, { href: '/reports', title: 'Reports', icon: Files }, { href: '/questions', title: 'Clarifications', icon: CircleHelp }, { href: '/response-estimates', title: 'Response estimates', icon: Clock3 }, { href: '/activity', title: 'Activity history', icon: History }]
  const props = { revision, refresh }
  function content() {
    if (path === '/questions') return <ClarificationsPage {...props} funder={!!funder} />
    if (funder) return <SharedPage {...props} />
    if (path.startsWith('/grants/')) return <GrantPage {...props} grantId={decodeURIComponent(path.split('/')[2])} />
    if (path === '/evidence') return <EvidencePage {...props} />
    if (path === '/decisions') return <DecisionsPage {...props} />
    if (path === '/reports') return <ReportsPage {...props} />
    if (path === '/financials') return <FinancialsPage {...props} />
    if (path === '/response-estimates') return <ResponseEstimatesPage revision={revision} />
    if (path === '/activity') return <ActivityHistoryPage revision={revision} />
    return <PortfolioPage {...props} user={user!} />
  }
  const identities = <div className="identity-options"><button disabled={busy} onClick={() => login('brightpath')}><span className="avatar">BP</span><span><strong>Bright Path Lab</strong><small>Grant administrator · three grants</small></span><ArrowRight size={18} /></button><button disabled={busy} onClick={() => login('harbour')}><span className="avatar lavender">HC</span><span><strong>Harbour Collective</strong><small>Grant administrator · one grant</small></span><ArrowRight size={18} /></button><button disabled={busy} onClick={() => login('northstar')}><span className="avatar gold">NF</span><span><strong>Northstar Foundation</strong><small>Funder · shared reports only</small></span><ArrowRight size={18} /></button></div>
  if (booting) return <div className="boot"><Logo /><Loading text="Connecting to GrantThread…" /></div>
  if (!user) {
    const setupPending = !local && !cloudConfigured
    return <div className="login-page">
      <div className="login-story"><Logo /><div className="login-copy"><div className="eyebrow">A little less administration.</div><h1>Many grants.<br />One clear thread.</h1><p>Connect your spending, evidence and reports.<br />Keep the decisions that matter in human hands.</p><div className="thread-steps"><span><FileStack size={19} />Record once</span><i /><span><CheckCheck size={19} />Review together</span><i /><span><Files size={19} />Report clearly</span></div></div><div className="login-footer"><ShieldCheck size={16} />Purposeful sharing. Clear accountability.</div></div>
      <div className="login-panel">
        <Badge tone="warning">{local ? 'Synthetic demonstration data' : setupPending ? 'Website preview' : 'Secure workspace'}</Badge>
        <h2>{setupPending ? <>Your site is here.<br />The workspace is next.</> : <>Your workspace,<br />with the whole picture.</>}</h2>
        <p className="muted">{local ? 'Choose a demonstration identity to explore the complete reporting workflow.' : setupPending ? 'The website files are available. Secure sign-in and a workspace server still need to be connected before you can test your records.' : 'Sign in to your organisation’s secure workspace.'}</p>
        {setupPending ? <section className="connection-card" aria-labelledby="connection-title">
          <h3 id="connection-title">Setup is not finished</h3>
          <ul><li><CheckCheck size={17} /><span>Website interface loaded</span></li><li><Clock3 size={17} /><span>Sign-in, financial records and uploads await connection</span></li><li><ShieldCheck size={17} /><span>File uploads are unavailable in this preview</span></li></ul>
          <p>The site owner needs to connect the backend and upload a configured website package. Reloading this preview alone will not finish setup.</p>
        </section> : connectionError ? <Notice>The workspace server is unavailable right now. Check your internet connection, then try connecting again. If this continues, the site owner needs to check the server connection.</Notice> : null}
        {error && <Notice>{error}</Notice>}
        {local ? identities : !setupPending && !connectionError ? <button className="button primary full" disabled={busy} onClick={() => { setBusy(true); signInCloud().catch(e => { setError(e.message); setBusy(false) }) }}>Sign in securely<ArrowRight size={18} /></button> : null}
        {(setupPending || connectionError) && <details className="connection-details"><summary>Connection details for the site owner</summary><dl><div><dt>Website address</dt><dd>{location.origin}{location.pathname}</dd></div><div><dt>Workspace server</dt><dd>{apiUrl('/health')}</dd></div><div><dt>Secure sign-in</dt><dd>{cloudConfigured ? 'Public settings are present; sign-in still needs verification.' : 'Public sign-in settings are missing from this build.'}</dd></div></dl>{connectionError && <p>{connectionError}</p>}<p>Cloud setup requires the deployed API address and Cognito sign-in settings, followed by a new build. Local testing requires the local API server.</p></details>}
        {(local || !setupPending && !connectionError) && <div className="login-note"><ActivityIcon size={17} /><p>{local ? 'Demonstration identities and initial portfolio records are fictional. Uploaded records may contain real data and remain scoped to your organisation.' : 'Sign-in gives you access to the records and reports shared with your organisation.'}</p></div>}
        {(setupPending || connectionError) && <button className="text-button connection-retry" onClick={() => setConnectionAttempt(value => value + 1)}><RefreshCw size={14} />Check connection again</button>}
      </div>
    </div>
  }
  return <div className="app-shell"><a className="skip-link" href="#main" onClick={e => { e.preventDefault(); document.getElementById("main")?.focus() }}>Skip to content</a><aside id="workspace-sidebar" className={`sidebar ${mobileOpen ? 'open' : ''}`}><div className="sidebar-brand"><Logo /><button id="close-mobile-navigation" className="icon-button mobile-only" onClick={closeMobileNavigation} aria-label="Close navigation"><X size={20} /></button></div><button className="workspace-switch" onClick={() => setIdentityOpen(true)}><span className="org-symbol"><Building2 size={19} /></span><span><strong>{user.organisationName}</strong><small>{funder ? 'Funder workspace' : 'Grantee workspace'}</small></span><ChevronDown size={14} /></button><div className="nav-caption">WORKSPACE</div><nav aria-label="Main navigation">{nav.map(item => <a key={item.href} href={`#${item.href}`} onClick={() => { if (mobileOpen && item.href === path) { pendingNavigationFocus.current = 'main'; setMobileOpen(false) } }} aria-current={path === item.href || item.href === '/' && path.startsWith('/grants/') ? 'page' : undefined} className={path === item.href || item.href === '/' && path.startsWith('/grants/') ? 'active' : ''}><item.icon size={19} /><span>{item.title}</span>{item.href === '/decisions' && <span className="nav-spark" />}</a>)}</nav><div className="sidebar-bottom"><div className="purpose-note"><Network size={24} /><strong>Every fact has a thread.</strong><p>Follow it from evidence<br />to a shared report.</p></div><button className="profile-button" onClick={() => setIdentityOpen(true)}><span className="avatar small">{user.name.split(' ').map(s => s[0]).slice(0, 2).join('')}</span><span><strong>{user.name}</strong><small>{funder ? 'Programme officer' : 'Grant administrator'}</small></span><ChevronDown size={14} /></button></div></aside>{mobileOpen && <button className="nav-backdrop" onClick={closeMobileNavigation} aria-label="Close navigation" />}<div className="workspace" inert={mobileOpen || undefined}><div className="topbar"><div className="topbar-context"><button ref={menuButton} className="icon-button mobile-only" aria-expanded={mobileOpen} aria-controls="workspace-sidebar" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20} /></button><span>Workspace</span><span className="slash">/</span><strong>{nav.find(n => n.href === path)?.title || 'Grant detail'}</strong></div><div className="demo-label"><span />{funder ? 'Funder workspace' : 'Grantee workspace'}</div></div><main id="main" tabIndex={-1} key={user.id}>{error && <Notice>{error}</Notice>}{content()}</main><footer className="app-footer"><span>GrantThread <span className="footer-dot">·</span> Many grants. One clear thread.</span><span>{local ? 'Local demonstration' : 'Connected workspace'}<ArrowUpRight size={12} /></span></footer></div>{identityOpen && <Modal title="Your workspace" close={() => setIdentityOpen(false)}><div className="modal-body"><p>Signed in as <strong>{user.name}</strong> at {user.organisationName}.</p>{local && <><p className="muted">Switching identities establishes a new server-authorised session.</p>{identities}</>}<div className="dialog-actions spread"><button className="button secondary" onClick={logout}><LogOut size={16} />Sign out</button>{local && !funder && <button className="text-button danger" onClick={() => { setIdentityOpen(false); setResetOpen(true) }}>Reset local workspace</button>}</div></div></Modal>}{resetOpen && <Modal title="Reset this local workspace?" close={() => setResetOpen(false)}><div className="modal-body"><p>This resets this local workspace, including imported files, entered financial records, evidence, approvals, reports and questions. Records you added may contain real data. Other local sessions are invalidated.</p><div className="dialog-actions"><button className="button secondary" onClick={() => setResetOpen(false)}>Cancel</button><button className="button danger-button" disabled={busy} onClick={async () => { setBusy(true); try { await api('/demo/reset', { confirm: true }); setResetOpen(false); refresh() } catch (e) { setError((e as Error).message) } finally { setBusy(false) } }}>Reset local workspace</button></div></div></Modal>}</div>
}
