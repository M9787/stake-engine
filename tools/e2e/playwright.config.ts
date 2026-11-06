// e2e gate (docs/10 M6c/M6e). Runs the game on the Vite dev server with the local mock RGS
// (game\web\seventh-veil\dev\mockRgs.js). Session tokens in sessionID set mock conditions.
// Run: Push-Location tools\e2e; pnpm exec playwright test; Pop-Location
import path from 'node:path';
import { defineConfig } from '@playwright/test';

const APP_DIR = path.resolve(import.meta.dirname, '../../web-sdk/apps/seventh-veil');

export default defineConfig({
	testDir: './tests',
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
