import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const tmp = mkdtempSync(join(tmpdir(), 'heary-drawy-contracts-'));
const generatedPath = join(tmp, 'contracts.ts');

try {
  execFileSync(
    'npx',
    [
      'json2ts',
      '-i',
      'contracts/schema.json',
      '-o',
      generatedPath,
      '--bannerComment',
      '/* Generated from contracts/schema.json. Do not edit by hand. */',
    ],
    { stdio: 'inherit' },
  );

  const expected = readFileSync(generatedPath, 'utf8');
  const current = readFileSync('apps/web/src/generated/contracts.ts', 'utf8');
  if (expected !== current) {
    console.error('apps/web/src/generated/contracts.ts is stale. Run npm run generate:contracts.');
    process.exit(1);
  }
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
