#!/usr/bin/env node
// Two-device demo on one Wi-Fi network: starts the API (local Postgres, a fresh Room and its
// passcode) and serves the web app over HTTPS on the LAN so iOS Safari allows the microphone.
//
//   npm run demo                      # Room lasts 8 hours
//   DEMO_HOST=192.168.1.20 npm run demo   # add an address this machine cannot see itself (e.g. WSL)
//
// Adults and synthetic data only. Ctrl+C stops everything.
import { spawn } from 'node:child_process';
import { networkInterfaces } from 'node:os';
import { fileURLToPath } from 'node:url';

const PORT = 5173;
const root = fileURLToPath(new URL('..', import.meta.url));

const lanAddresses = Object.values(networkInterfaces())
  .flat()
  .filter((address) => address && address.family === 'IPv4' && !address.internal)
  .map((address) => address.address);
const extraHosts = (process.env.DEMO_HOST ?? '').split(',').map((host) => host.trim()).filter(Boolean);
const hosts = [...new Set([...extraHosts, ...lanAddresses])];
// The room socket only accepts pages it knows, so allow exactly the addresses we serve.
const origins = ['localhost', '127.0.0.1', ...hosts].map((host) => `https://${host}:${PORT}`);

const children = [
  spawn('npm', ['run', 'dev:api:local', '--', '--room-hours', process.env.DEMO_ROOM_HOURS ?? '8'], {
    cwd: root,
    stdio: 'inherit',
    detached: true,
    env: { ...process.env, ALLOWED_ORIGINS: origins.join(',') },
  }),
  spawn(`${root}node_modules/.bin/vite`, ['--host', '0.0.0.0', '--port', String(PORT), '--strictPort'], {
    cwd: `${root}apps/web`,
    stdio: 'inherit',
    detached: true,
    env: { ...process.env, DEMO_HTTPS: '1' },
  }),
];

console.log(`
Heary Drawy demo
  Open on the iPad and iPhone (same Wi-Fi): ${hosts.map((host) => `https://${host}:${PORT}`).join('  or  ') || '(no network address found)'}
  The certificate is self-signed: tap "Show Details" > "visit this website" once on each device.
  A grown-up enters the Room passcode printed below by the API.
  AI feedback: ${process.env.DEEPSEEK_API_KEY ? 'on (DEEPSEEK_API_KEY is set)' : 'off - rounds show the neutral result'}
`);

let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  // Each child leads its own process group, so npm/uv wrappers and the servers under them all stop.
  for (const child of children) {
    try {
      process.kill(-child.pid, 'SIGINT');
    } catch {
      // Already gone.
    }
  }
  setTimeout(() => process.exit(code), 3000).unref();
}
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
for (const child of children) {
  child.on('exit', (code) => stop(code ?? 1));
  child.on('error', (error) => {
    console.error(error.message);
    stop(1);
  });
}
