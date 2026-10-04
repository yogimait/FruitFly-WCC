import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // Must be declared here as well as in tsconfig.app.json: tsc reads `paths`,
    // Vite does not. Without this the dev server fails to resolve `@/...`
    // while the type check passes.
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // The measurement API is served by scripts/serve.py on :8765. Proxying it in dev lets
    // `bun run dev` and `serve.py` run side by side with no CORS setup.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8768',
        changeOrigin: true,
      },
    },
  },
})