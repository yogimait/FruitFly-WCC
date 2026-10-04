import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

// No dev proxy. The measurement is produced offline by scripts/measure_final.py and copied
// into public/api by scripts/export_static.py, so `bun run dev` and a deployed static build
// read the identical files by the identical path. One code path, no port to keep in sync.
//
// Earlier this proxied /api to scripts/serve.py on :8768, which meant the dashboard went blank
// whenever that process was not running, and dev behaved differently from production.
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
})