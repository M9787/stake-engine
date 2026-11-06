// M6e book replay (docs/10 M6e): for every mode and outcome category, play a forced round on the
// mock RGS, then open the Engine replay URL for that round (docs/08 [171][172]) and play it through.
// Checks: the play response carries the forced book; the replay's final win
// (stateBet.winBookEventAmount, book units) equals the book payoutMultiplier; no page errors,
// console errors, failed or >= 400 requests; no error modal; the replay sends no wallet request.
// Run: Push-Location tools\e2e; pnpm exec playwright test tests/replay.spec.ts; Pop-Location (~35 min)
// Force keys come from .mock-rgs/<mode>.json "forced" (scripts\books_to_mock.py).
import fs from 'node:fs';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

import { errorText, gameUrl, openGame, sv } from './helpers';

const MOCK_DIR = path.resolve(import.meta.dirname, '../../../web-sdk/apps', process.env.APP ?? 'cluster-tumble', '.mock-rgs', process.env.GAME ?? 'seventh_veil');
// Game id and modes from the skin (build/<GAME>/web/modes.json, tools/gen/gen_skin_ts.py).
const GAME = process.env.GAME ?? 'seventh_veil';
const SKIN = JSON.parse(fs.readFileSync(path.resolve(import.meta.dirname, '../../../build', GAME, 'web', 'modes.json'), 'utf-8'));
const MODES: string[] = SKIN.modes.map((m: { name: string }) => m.name);
const TEXTS: Record<string, string> = JSON.parse(
	fs.readFileSync(path.resolve(import.meta.dirname, '../../../build', GAME, 'web', 'rules.generated.en.json'), 'utf-8'),
).texts;
// REPLAY_FULL=1 also plays the normal round to the end (about twice the runtime).
const FULL = !!process.env.REPLAY_FULL;
const CATEGORIES = ['loss', 'win', 'big', 'bonus', 'maxwin'] as const;

type Mock = { cost: number; forced: Record<string, number>; payout: Record<string, number> };
const mock: Record<string, Mock> = {};
for (const mode of MODES) {
	const data = JSON.parse(fs.readFileSync(path.join(MOCK_DIR, `${mode}.json`), 'utf-8'));
	const payout: Record<string, number> = {};
	for (const [key, id] of Object.entries<number>(data.forced)) {
		if (id !== null && data.books[id]) payout[key] = data.books[id].payoutMultiplier;
	}
	mock[mode] = { cost: data.cost, forced: data.forced, payout };
}

/** Collects every error signal on the page from now on. */
const watchErrors = (page: Page) => {
	const errors: string[] = [];
	const wallet: string[] = [];
	page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
	page.on('console', (m) => {
		if (m.type() === 'error') errors.push(`console: ${m.text()}`);
	});
	page.on('requestfailed', (r) => errors.push(`requestfailed: ${r.url()} ${r.failure()?.errorText}`));
	page.on('response', (r) => {
		if (r.status() >= 400) errors.push(`http ${r.status()}: ${r.url()}`);
	});
	page.on('request', (r) => {
		if (r.url().includes('/rgs/wallet/')) wallet.push(r.url());
	});
	return { errors, wallet };
};

/** Press through bonus intro/outro until the round has started and the game is idle again. */
const playThrough = async (page: Page, started: () => Promise<boolean>, timeout: number) => {
	const canvas = page.locator('canvas').first();
	let seenStart = false;
	await expect
		.poll(
			async () => {
				if (!seenStart) seenStart = await started();
				if (seenStart && (await sv<boolean>(page, 'sv.isIdle()'))) return true;
				await canvas.click({ position: { x: 640, y: 360 } }).catch(() => undefined);
				return false;
			},
			{ timeout, intervals: [1000] },
		)
		.toBe(true);
};

for (const mode of MODES) {
	const KEY = mode.toUpperCase();
	for (const category of CATEGORIES) {
		test(`replay ${mode} ${category}`, async ({ page, request }) => {
			test.setTimeout(420_000);
			const m = mock[mode];
			test.skip(!(category in m.payout), `.mock-rgs/${mode}.json has no "${category}" book`);
			const expected = m.payout[category];
			const isBuy = m.cost >= 10;
			await page.emulateMedia({ reducedMotion: 'reduce' }); // starts in turbo

			// 1. Normal play of the forced book.
			const url = gameUrl(['b100000']);
			const sessionID = new URL(url, 'https://x').searchParams.get('sessionID')!;
			const play = watchErrors(page);
			await openGame(page, url);
			expect(await sv<boolean>(page, 'sv.stateBet.isTurbo')).toBe(true);
			await request.post('https://localhost:3007/rgs/mock/force', { data: { sessionID, next: category } });
			const playResponse = page.waitForResponse((r) => r.url().includes('/rgs/wallet/play'));
			if (isBuy) {
				// Buy path as a player takes it: bonus menu -> mode card -> confirm.
				const title = TEXTS[`mode.${KEY.toLowerCase()}.title`];
				await sv(page, "(sv.stateModal.modal = { name: 'buyBonus' }, true)");
				// The modal markup is rendered twice; the last copy is the one on top.
				const card = page.locator('.title', { hasText: title }).last().locator('xpath=ancestor::*[.//button][1]');
				await card.locator('button').first().click();
				await page.locator('[data-test="confirm-button"]').last().click();
			} else {
				await sv(page, `(sv.stateBet.activeBetModeKey = '${KEY}', true)`);
				await page.keyboard.press('Space');
			}
			const round = (await (await playResponse).json()).round;
			expect(round.mode).toBe(KEY);
			expect(Math.round(round.payoutMultiplier * 100)).toBe(expected);
			if (FULL) {
				await playThrough(page, async () => true, 300_000);
				expect(await sv<number>(page, 'sv.stateBet.winBookEventAmount')).toBe(expected);
			}
			expect(await errorText(page)).toBe('');
			expect(play.errors).toEqual([]);

			// 2. Replay of the same round (Engine replay URL; no session, no bet).
			await page.goto('about:blank');
			const replay = watchErrors(page);
			const replayResponse = page.waitForResponse((r) => r.url().includes('/rgs/bet/replay/'));
			const replayUrl =
				`/?replay=true&game=${SKIN.gameId}&version=1&mode=${KEY}&event=${round.roundID}` +
				`&rgs_url=localhost:3007/rgs&amount=${round.amount}&currency=USD&lang=en`;
			await page.goto(replayUrl);
			const data = await (await replayResponse).json();
			expect(data.payout).toBe(round.payout);
			await page.waitForFunction(() => (globalThis as any).__sv, null, { timeout: 60_000 });
			await sv(page, '(sv.stateBet.isTurbo = true, true)');
			// The resume machine clears betToResume when the replayed round starts.
			await playThrough(page, () => sv<boolean>(page, 'sv.stateBet.betToResume === null'), 300_000);
			expect(await sv<number>(page, 'sv.stateBet.winBookEventAmount')).toBe(expected);
			expect(await sv<string>(page, 'sv.stateBet.activeBetModeKey')).toBe(KEY);
			expect(await errorText(page)).toBe('');
			expect(replay.errors).toEqual([]);
			expect(replay.wallet).toEqual([]);
		});
	}
}
