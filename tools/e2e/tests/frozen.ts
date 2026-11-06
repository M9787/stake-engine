import { expect, type Page } from '@playwright/test';

/**
 * Deterministic game frames for screenshot baselines (docs/10 plan v3.3, slice 10.2a).
 * - Math.random is replaced by a seeded generator before any app script runs.
 * - Playwright's fake clock is installed before navigation, so Pixi tickers, Spine and timers only move
 *   when the test advances time. Loading still needs real network, so the test advances fake time in
 *   fixed steps while it waits, then a fixed amount after the click, before each screenshot.
 */
export const openGameFrozen = async (page: Page, url: string, settleMs = 3000) => {
	await page.addInitScript(() => {
		let s = 0x7777;
		Math.random = () => {
			s = (s * 1664525 + 1013904223) >>> 0;
			return s / 4294967296;
		};
	});
	await page.clock.install({ time: new Date('2026-11-07T00:00:00Z') });
	await page.goto(url);
	const canvas = page.locator('canvas').first();
	for (let i = 0; i < 120; i++) {
		await page.clock.runFor(250);
		// Vite may reload the page once on a cold dependency cache; treat that as 'not ready yet'.
		if (await page.evaluate(() => Boolean((globalThis as any).__sv)).catch(() => false)) break;
		await page.waitForTimeout(250);
	}
	await expect(canvas).toBeVisible({ timeout: 60_000 });
	// Loading screen: advance fake time and click until the game scene replaces it.
	for (let i = 0; i < 160; i++) {
		await page.clock.runFor(250);
		const loading = await page.evaluate(() => (globalThis as any).__sv?.loadingScreen?.() !== false).catch(() => true);
		if (!loading) break;
		if (i % 4 === 3) await canvas.click().catch(() => undefined);
		await page.waitForTimeout(250);
	}
	await page.clock.runFor(settleMs);
};
