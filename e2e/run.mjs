#!/usr/bin/env node
// Local e2e harness: backend in Docker + app in Expo Go on the iOS Simulator + Maestro.
//
// Requires (host tools, install once):
//   - Maestro (https://maestro.mobile.dev)
//   - Docker Desktop
//   - Xcode with an iOS Simulator already booted (Simulator.app)
//
// Usage: node e2e/run.mjs [maestro test args...]

import { execSync, spawn, spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const BACKEND_DIR = path.join(ROOT_DIR, 'backend');
const MOBILE_DIR = path.join(ROOT_DIR, 'mobile');
const FLOWS_DIR = path.join(ROOT_DIR, 'e2e', 'flows');
const EXPO_APP_ID = 'host.exp.Exponent'; // Expo Go's bundle id
const EXPO_URL = 'exp://127.0.0.1:8081';

// Runs a command and returns its stdout, throwing on a non-zero exit code.
function sh(command, options = {}) {
  return execSync(command, { encoding: 'utf8', ...options });
}

// Same as sh(), but ignores a non-zero exit code (e.g. "terminate" on an app that isn't running).
function shOrIgnore(command, options = {}) {
  try {
    return sh(command, { stdio: 'pipe', ...options });
  } catch {
    return '';
  }
}

async function waitUntil(label, timeoutMs, check) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await check()) return;
    await sleep(1000);
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function isUp(url, mustInclude) {
  try {
    const res = await fetch(url);
    if (!mustInclude) return true; // any response means the server is up
    return (await res.text()).includes(mustInclude);
  } catch {
    return false;
  }
}

function resetParticipant() {
  const output = sh('docker compose exec -T web python manage.py reset_participant', { cwd: BACKEND_DIR });
  console.log(output.trim());
  const code = output.match(/new code: (\S+)/)?.[1];
  if (!code) throw new Error(`Could not parse enrollment code from: ${output}`);
  return code;
}

async function ensureMetroRunning() {
  if (await isUp('http://localhost:8081/status', 'packager-status:running')) {
    console.log('==> Reusing already-running Metro bundler on :8081');
    return { startedByUs: false };
  }

  console.log('==> Starting Metro + Expo Go on the iOS Simulator');
  const child = spawn('npx', ['expo', 'start', '--ios', '--go', '--localhost'], {
    cwd: MOBILE_DIR,
    stdio: 'ignore',
    detached: true,
  });
  child.unref();

  await waitUntil('Metro on :8081', 60_000, () => isUp('http://localhost:8081/status', 'packager-status:running'));
  return { startedByUs: true };
}

function runMaestroFlow(flowPath, enrollmentCode, extraArgs) {
  const result = spawnSync(
    'maestro',
    ['test', flowPath, '-e', `ENROLLMENT_CODE=${enrollmentCode}`, '-e', `EXPO_APP_ID=${EXPO_APP_ID}`, ...extraArgs],
    { stdio: 'inherit' }
  );
  return result.status === 0;
}

async function main() {
  const extraArgs = process.argv.slice(2);

  console.log('==> Checking for a booted iOS Simulator');
  if (!sh('xcrun simctl list devices booted').includes('Booted')) {
    console.error('No booted simulator found. Open Simulator.app and re-run.');
    process.exit(1);
  }

  console.log('==> Pre-granting microphone permission to Expo Go (avoids a system dialog mid-flow)');
  sh(`xcrun simctl privacy booted grant microphone ${EXPO_APP_ID}`);

  console.log('==> Starting backend (docker compose)');
  sh('docker compose up -d', { cwd: BACKEND_DIR, stdio: 'inherit' });

  console.log('==> Waiting for backend to respond on :8000');
  await waitUntil('backend on :8000', 30_000, () => isUp('http://localhost:8000/api/'));

  const metro = await ensureMetroRunning();

  console.log('==> Running Maestro flows');
  const flows = readdirSync(FLOWS_DIR)
    .filter((f) => f.endsWith('.yaml'))
    .sort()
    .map((f) => path.join(FLOWS_DIR, f));

  let failed = false;
  for (const flow of flows) {
    const name = path.basename(flow);

    // Enrollment codes are single-use, so every flow gets its own fresh reset immediately
    // before it runs (each flow enrolls independently — the app has no "already enrolled"
    // bootstrap check, so it always starts at the Enrollment screen).
    console.log(`----> Resetting participant for ${name}`);
    const code = resetParticipant();

    // Force-terminate before deep-linking: a native Alert (e.g. a leftover "Invalid code"
    // dialog) is a system modal that survives a JS bundle reload, and would otherwise block
    // the next flow. Expo Go's own `openLink` isn't reliable for exp:// links from within a
    // Maestro flow, so we deep-link via simctl instead and the flow starts already-loaded.
    console.log('----> Restarting Expo Go fresh and deep-linking to the dev server');
    shOrIgnore(`xcrun simctl terminate booted ${EXPO_APP_ID}`);
    sh(`xcrun simctl openurl booted "${EXPO_URL}"`);

    console.log(`----> Running ${name} (code: ${code})`);
    if (!runMaestroFlow(flow, code, extraArgs)) failed = true;
  }

  if (metro.startedByUs) {
    console.log('==> Stopping Metro/Expo Go (started by this script)');
    shOrIgnore('pkill -f "expo start --ios"');
  }

  process.exit(failed ? 1 : 0);
}

main();
