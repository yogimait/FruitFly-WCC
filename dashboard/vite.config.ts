import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

export default defineConfig(({ command }) => ({
  plugins: [react(), tailwindcss()],
  resolve: {
    // Must be declared here as well as in tsconfig.app.json: tsc reads `paths`,
    // Vite does not. Without this the dev server fails to resolve `@/...`
    // while the type check passes.
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // The measurement API is served by scripts/serve.py on :8768 during `bun run dev`, so the
  // two can run side by side. In `vite preview` and `vite build` there is no Python process,
  // and /api is served from public/api as static files by export_static.py — proxying there
  // would return 502 for every request.
  server:
    command === 'serve'
      ? {
          proxy: {
            '/api': {
              target: 'http://127.0.0.1:8768',
              changeOrigin: true,
            },
          },
        }
      : undefined,
  preview:
    command === 'serve'
      ? undefined
      : undefined,
}))