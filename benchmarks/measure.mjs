// Run from a generated frontend after installing dependencies and generating API types.
import { chromium } from '@playwright/test';
import { execFileSync, spawn } from 'node:child_process';
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { gzipSync, brotliCompressSync, constants } from 'node:zlib';
import { setTimeout as delay } from 'node:timers/promises';

const [label, revision, output] = process.argv.slice(2);
const base = 'http://127.0.0.1:5173';
const started = performance.now();
execFileSync('pnpm', ['build'], { stdio: 'inherit' });
const buildMs = performance.now() - started;

const files = readdirSync('dist', { recursive: true })
  .filter(file => /\.(?:js|mjs|css)$/.test(file));
const assets = { js: { raw: 0, gzip: 0, brotli: 0 }, css: { raw: 0, gzip: 0, brotli: 0 } };
for (const file of files) {
  const data = readFileSync(resolve('dist', file));
  const total = file.endsWith('.css') ? assets.css : assets.js;
  total.raw += data.length;
  total.gzip += gzipSync(data, { level: 9 }).length;
  total.brotli += brotliCompressSync(data, {
    params: { [constants.BROTLI_PARAM_QUALITY]: 11 },
  }).length;
}

async function ready(url) {
  for (let attempt = 0; attempt < 120; attempt++) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      // Servers are starting.
    }
    await delay(250);
  }
  throw new Error('Server not ready: ' + url);
}
const api = spawn('uv', ['run', 'python', '-m', 'app.cli', 'serve'], {
  cwd: '..', env: { ...process.env, APP_DATABASE: 'data/benchmark.sqlite3' },
  detached: true, stdio: 'inherit',
});
const preview = spawn('pnpm', ['preview'], { detached: true, stdio: 'inherit' });
let browser;
try {
  await ready('http://127.0.0.1:8000/api/health/live');
  await ready(base);
  const note = 'Benchmark readiness marker';
  const response = await fetch(base + '/api/notes', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: note }),
  });
  if (!response.ok) throw new Error('Failed to seed benchmark database');
  browser = await chromium.launch();
  const samples = [];
  for (let run = 0; run < 9; run++) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    await page.goto(base, { waitUntil: 'domcontentloaded' });
    // Same meaningful readiness condition for all implementations: real API note rendered.
    const handle = await page.waitForFunction(text =>
      Array.from(document.querySelectorAll('button')).some(b => b.textContent?.trim() === text)
        ? performance.now() : false, note);
    const readyMs = await handle.jsonValue();
    await page.waitForFunction(() => performance.getEntriesByName('first-contentful-paint').length > 0);
    const metrics = await page.evaluate(() => ({
      fcpMs: performance.getEntriesByName('first-contentful-paint')[0].startTime,
      initialJsBytes: performance.getEntriesByType('resource')
        .filter(r => /\.(?:js|mjs)$/.test(new URL(r.name).pathname))
        .reduce((sum, r) => sum + r.encodedBodySize, 0),
    }));
    samples.push({ readyMs, ...metrics });
    await context.close();
  }
  const median = key => samples.map(s => s[key]).sort((a, b) => a - b)[4];
  const result = { label, revision, buildMs, assets, median: {
    readyMs: median('readyMs'), fcpMs: median('fcpMs'), initialJsBytes: median('initialJsBytes'),
  }, samples, node: process.version, chromium: browser.version() };
  writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result));
} finally {
  await browser?.close();
  for (const child of [preview, api]) {
    if (child.pid) {
      try { process.kill(-child.pid, 'SIGTERM'); } catch (error) {
        if (error.code !== 'ESRCH') throw error;
      }
    }
  }
}
