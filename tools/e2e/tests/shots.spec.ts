// Reviewer-size screenshots (docs/10 M6c HUD overlap, M6e). Output: tools\e2e\shots\ (git-ignored).
import { test } from '@playwright/test';

import { gameUrl, openGame } from './helpers';

for (const [w, h] of [
	[1280, 720],
	[1200, 675],
	[400, 225],
	[425, 812],
] as const) {
	test(`screenshot ${w}x${h}`, async ({ page }) => {
		await page.setViewportSize({ width: w, height: h });
		await openGame(page, gameUrl());
		await page.waitForTimeout(2000);
		await page.screenshot({ path: `shots/${w}x${h}.png` });
	});
}
