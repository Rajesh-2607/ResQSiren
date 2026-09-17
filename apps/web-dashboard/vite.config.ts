import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Public caller flow only — /emergency (report + status) and
      // /dispatch/{id}/location (driver GPS relay). Anchored to `/dispatch`
      // exactly or `/dispatch/...` — a plain prefix match would also catch
      // stray navigation to the old `/dispatcher` URL and 404 instead of
      // falling through to the SPA's catch-all redirect.
      '/emergency': 'http://localhost:4000',
      '^/dispatch($|/)': 'http://localhost:4000',
      '/socket.io': {
        target: 'http://localhost:4000',
        ws: true,
      },
    },
  },
})
