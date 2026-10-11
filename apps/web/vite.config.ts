import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import basicSsl from '@vitejs/plugin-basic-ssl';

// `npm run demo` sets DEMO_HTTPS so phones on the LAN get a secure page (iOS needs it for the mic).
const https = process.env.DEMO_HTTPS === '1';

export default defineConfig({
  plugins: [react(), ...(https ? [basicSsl()] : [])],
  // The 3D viewer (model-viewer + three.js, ~1 MB) is its own lazy chunk, loaded only on the
  // Speaker's play screen; the warning limit sits just above it so a larger main bundle still warns.
  build: { chunkSizeWarningLimit: 1100 },
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
