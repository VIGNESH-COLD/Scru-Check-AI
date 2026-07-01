import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        // Bind to all interfaces so the app is reachable from LAN / ngrok / public IP.
        // Access via http://<your-ip>:5173 from any device on the same network.
        host: '0.0.0.0',
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true
            }
            // NOTE: /external/* is intentionally NOT proxied here.
            // App.jsx detects window.location.pathname.includes('/external/')
            // and renders ExternalViewer, which calls /api/external/view/{token} itself.
        }
    }
})
