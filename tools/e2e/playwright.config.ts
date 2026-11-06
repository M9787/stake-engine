// e2e gate (docs/10 M6c/M6e). Runs the game on the Vite dev server with the local mock RGS
// (core\web\cluster-tumble\dev\mockRgs.js). Session tokens in sessionID set mock conditions.
// Run: Push-Location tools\e2e; pnpm exec playwright test; Pop-Location
import path from 'node:path';
import { defineConfig } from '@playwright/test';

// GAME selects the skin ($skin -> build\<GAME>\web); APP is the one synced core app.
const GAME = process.env.GAME ?? 'seventh_veil';
const APP = process.env.APP ?? 'cluster-tumble';
export const APP_DIR = path.resolve(import.meta.dirname, '../../web-sdk/apps', APP);

export default defineConfig({
	testDir: './tests',
	snapshotPathTemplate: `{testDir}/../baselines/${GAME}/{arg}{ext}`,
	expect: {
		toHaveScreenshot: { maxDiffPixelRatio: 0.01, animations: 'disabled', caret: 'hide' },
	},
	timeout: 90_000,
	workers: 1,
	reporter: [['list']],
	use: {
		baseURL: 'https://localhost:3007',
		ignoreHTTPSErrors: true,
		viewport: { width: 1280, height: 720 },
	},
	webServer: {
		command: 'pnpm exec vite dev --port 3007',
		cwd: APP_DIR,
		url: 'https://localhost:3007',
		ignoreHTTPSErrors: true,
		reuseExistingServer: true,
		timeout: 180_000,
	},
});
