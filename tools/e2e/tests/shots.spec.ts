// Reviewer-size screenshots (docs/10 M6c HUD overlap, M6e). Output: build\<GAME>\shots\<w>x<h>.png
// (git-ignored; tools\release\pack.py embeds them in the submission pack). GAME defaults to seventh_veil.
import fs from 'node:fs';
import path from 'node:path';
import { test } from '@playwright/test';

import { gameUrl, openGame } from './helpers';

const GAME = process.env.GAME ?? 'seventh_veil';
const OUT = path.resolve(import.meta.dirname, '../../../build', GAME, 'shots');

for (const [w, h] of [
	[1280, 720],
	[1200, 675],
	[400, 225],
	[425, 812],
] as const) {
	test(`screenshot ${w}x${h}`, async ({ page }) => {
		fs.mkdirSync(OUT, { recursive: true });
		await page.setViewportSize({ width: w, height: h });
		await openGame(page, gameUrl());
		await page.waitForTimeout(2000);
		await page.screenshot({ path: path.join(OUT, `${w}x${h}.png`) });
	});
}
