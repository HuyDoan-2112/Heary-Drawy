#!/usr/bin/env node
// Two-device demo on one Wi-Fi network: starts the API (local Postgres, a fresh Room and its
// passcode) and serves the web app over HTTPS on the LAN so iOS Safari allows the microphone.
//
//   npm run demo                      # Room lasts 8 hours
//   DEMO_HOST=192.168.1.20 npm run demo   # add an address this machine cannot see itself
//   On Windows WSL (NAT networking) the Windows Wi-Fi address is found automatically, and the
//   script prints the one-time PowerShell lines that forward it into WSL.
//   DEEPSEEK_API_KEY in .env (git-ignored) turns on AI feedback; Whisper runs locally either way.
//
// Adults and synthetic data only. Ctrl+C stops everything.
import { execFileSync, spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { networkInterfaces } from 'node:os';
import { fileURLToPath } from 'node:url';

const PORT = 5173;
const root = fileURLToPath(new URL('..', import.meta.url));

// Secrets such as DEEPSEEK_API_KEY live in the git-ignored .env file next to package.json.
try {
  process.loadEnvFile(`${root}.env`);
} catch {
  // No .env: AI feedback stays off and rounds show the neutral result.
}

const lanAddresses = Object.values(networkInterfaces())
  .flat()
  .filter((address) => address && address.family === 'IPv4' && !address.internal)
  .map((address) => address.address);

/** Under WSL the phones reach Windows, not this Linux VM: return Windows' Wi-Fi/LAN address. */
function windowsAddress() {
  try {
    if (!readFileSync('/proc/version', 'utf8').toLowerCase().includes('microsoft')) return null;
    const command = "(Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up' }).IPv4Address.IPAddress";
    const output = execFileSync('powershell.exe', ['-NoProfile', '-Command', command], { encoding: 'utf8', timeout: 15000 });
    return output.split(/\s+/).find((line) => /^\d+\.\d+\.\d+\.\d+$/.test(line)) ?? null;
  } catch {
    return null;
  }
}

const windowsIp = windowsAddress();
// In WSL NAT mode the Windows address is not one of ours; only it is reachable from the devices.
const wslNat = windowsIp !== null && !lanAddresses.includes(windowsIp);
const extraHosts = (process.env.DEMO_HOST ?? '').split(',').map((host) => host.trim()).filter(Boolean);
const hosts = [...new Set([...extraHosts, ...(wslNat ? [windowsIp] : lanAddresses)])];
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
if (wslNat) {
  const wslIp = lanAddresses.find((address) => !address.startsWith('10.255.')) ?? lanAddresses[0];
  console.log(`  Running inside WSL: the devices reach Windows (${windowsIp}), which must forward to WSL (${wslIp}).
  If the devices cannot load the page, paste this into PowerShell opened with "Run as administrator"
  (again whenever WSL's address changes, e.g. after a restart):

    netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=${PORT} connectaddress=${wslIp} connectport=${PORT}
    New-NetFirewallRule -DisplayName "Heary Drawy demo" -Direction Inbound -Protocol TCP -LocalPort ${PORT} -Action Allow -ErrorAction SilentlyContinue
`);
}

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
