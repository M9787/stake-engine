import { expect, type Page } from '@playwright/test';

/** Game URL against the mock RGS. `tokens` are sessionID tokens (see dev/mockRgs.js). */
export const gameUrl = (tokens: string[] = [], extra = '') => {
	const sessionID = ['e2e', `${Date.now()}${Math.floor(Math.random() * 1e6)}`, ...tokens].join('_');
	return `/?sessionID=${sessionID}&rgs_url=localhost:3007/rgs&lang=en${extra}`;
};

/** Dev-only state handle set in Game.svelte (`globalThis.__sv`). */
export const sv = <T>(page: Page, fn: string) => page.evaluate(`(() => { const sv = globalThis.__sv; return ${fn}; })()`) as Promise<T>;

/** Open the game and pass the loading screen. Collects console errors. */
export const openGame = async (page: Page, url: string) => {
	const errors: string[] = [];
	page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
	await page.goto(url);
	await page.waitForFunction(() => (globalThis as any).__sv, null, { timeout: 60_000 });
	const canvas = page.locator('canvas').first();
	await expect(canvas).toBeVisible({ timeout: 60_000 });
	// Loading screen waits for a click once assets are in.
	for (let i = 0; i < 20; i++) {
		await page.waitForTimeout(1000);
		await canvas.click().catch(() => undefined);
		const ready = await page.evaluate(() => !document.body.innerText.includes('Loading'));
		if (ready && i > 2) break;
	}
	return errors;
};

/** Start a round with Space (Engine: Space places a bet unless disabledSpacebar). */
export const spin = async (page: Page) => {
	await page.keyboard.press('Space');
};

/** Visible error modal text, or '' if none. */
export const errorText = async (page: Page) =>
	(await page.locator('.error-text').first().textContent({ timeout: 1000 }).catch(() => '')) ?? '';
