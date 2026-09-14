import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode, command }) => {
  const fileEnv = loadEnv(mode, '.', '')
  // loadEnv includes shell-provided values, which take precedence over env files.
  const setting = (name: string, fallback = '') => fileEnv[name] ?? fallback
  const localDemo = command === 'serve' && setting('GRANTTHREAD_LOCAL_FRONTEND') === '1'
  const basePath = localDemo ? '/' : setting('VITE_BASE_PATH', './') || './'
  const publicConfig = localDemo ? { apiUrl: '/api', cognitoDomain: '', cognitoClientId: '', cognitoRedirectUri: '' } : {
    apiUrl: setting('VITE_API_URL', '/api') || '/api',
    cognitoDomain: setting('VITE_COGNITO_DOMAIN'),
    cognitoClientId: setting('VITE_COGNITO_CLIENT_ID'),
    cognitoRedirectUri: setting('VITE_COGNITO_REDIRECT_URI'),
  }
  return {
    plugins: [react(), {
      name: 'grantthread-build-manifest',
      enforce: 'post',
      async generateBundle(_options, bundle) {
        const assets = Object.fromEntries(await Promise.all(Object.entries(bundle).filter(([name]) => name === 'index.html' || name.startsWith('assets/')).sort(([a], [b]) => a.localeCompare(b)).map(async ([name, item]) => {
          const content = item.type === 'chunk' ? item.code : item.source
          const bytes = typeof content === 'string' ? new TextEncoder().encode(content) : new Uint8Array(content)
          const hash = await crypto.subtle.digest('SHA-256', bytes)
          return [name, Array.from(new Uint8Array(hash), value => value.toString(16).padStart(2, '0')).join('')]
        })))
        this.emitFile({ type: 'asset', fileName: 'grantthread-build.json', source: JSON.stringify({ schemaVersion: 1, mode, basePath, publicConfig, assets }, null, 2) + '\n' })
      },
    }],
    base: basePath,
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(publicConfig.apiUrl),
      'import.meta.env.VITE_COGNITO_DOMAIN': JSON.stringify(publicConfig.cognitoDomain),
      'import.meta.env.VITE_COGNITO_CLIENT_ID': JSON.stringify(publicConfig.cognitoClientId),
      'import.meta.env.VITE_COGNITO_REDIRECT_URI': JSON.stringify(publicConfig.cognitoRedirectUri),
    },
    server: { port: 5173, strictPort: true, proxy: { '/api': 'http://127.0.0.1:8000' } },
    build: { sourcemap: false },
  }
})
