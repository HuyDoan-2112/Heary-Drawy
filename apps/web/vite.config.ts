import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import basicSsl from '@vitejs/plugin-basic-ssl';

// `npm run demo` sets DEMO_HTTPS so phones on the LAN get a secure page (iOS needs it for the mic).
const https = process.env.DEMO_HTTPS === '1';

export default defineConfig({
  plugins: [react(), ...(https ? [basicSsl()] : [])],
  server: {
    proxy: {
      '/api/v1': { target: 'http://127.0.0.1:8000', ws: true },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
});
