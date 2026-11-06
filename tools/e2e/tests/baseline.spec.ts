// Screenshot baselines per game (docs/10 plan v3.3, slices 10.2a/10.2b). Frames are deterministic
// (frozen.ts). Baselines live in tools\e2e\baselines\<GAME>\ and are committed.
// Capture:  $env:GAME='seventh_veil'; Push-Location tools\e2e; pnpm exec playwright test baseline --update-snapshots; Pop-Location
// Verify:   $env:GAME='seventh_veil'; Push-Location tools\e2e; pnpm exec playwright test baseline; Pop-Location
import { expect, test } from '@playwright/test';

import { openGameFrozen } from './frozen';
import { gameUrl } from './helpers';

for (const [w, h] of [
	[1280, 720],
	[1200, 675],
	[400, 225],
	[425, 812],
] as const) {
	test(`baseline ${w}x${h}`, async ({ page }) => {
		await page.setViewportSize({ width: w, height: h });
		await openGameFrozen(page, gameUrl());
		await expect(page).toHaveScreenshot(`${w}x${h}.png`, {
			// Balance and bet amounts are fixed by the mock, but mask the HUD text row anyway (plan E2).
			mask: [page.locator('.balance, .bet-amount, [data-hud-amount]')],
		});
	});
}
