// M6c compliance checks against the mock RGS (docs/08 "Bets and balance", docs/10 M6c).
import fs from 'node:fs';
import path from 'node:path';
import { expect, test } from '@playwright/test';

import { errorText, gameUrl, openGame, spin, sv } from './helpers';

// Modes from the skin (build/<GAME>/web/modes.json): the maxBet check uses the first buy mode.
const GAME = process.env.GAME ?? 'seventh_veil';
const SKIN = JSON.parse(fs.readFileSync(path.resolve(import.meta.dirname, '../../../build', GAME, 'web', 'modes.json'), 'utf-8'));
const BUY = SKIN.modes.filter((m: { kind: string }) => m.kind === 'buy').map((m: { key: string }) => m.key) as string[];
const SPIN = (SKIN.modes.find((m: { cost: number }) => m.cost === 1) ?? SKIN.modes[0]).key as string;

const playRequests = (page: import('@playwright/test').Page) => {
	const list: number[] = [];
	page.on('response', (r) => {
		if (r.url().includes('/rgs/wallet/play')) list.push(r.status());
	});
	return list;
};

for (const [token, status, message] of [
	['paused', 423, 'paused for maintenance'],
	['gen', 500, 'Server error'],
	['gle', 400, 'Gambling limit reached'],
] as const) {
	test(`error ${token}: player message, no raw JSON`, async ({ page }) => {
		const plays = playRequests(page);
		await openGame(page, gameUrl([token]));
		await spin(page);
		await expect.poll(() => errorText(page), { timeout: 15_000 }).toContain(message);
		expect(plays).toContain(status);
		await expect(page.locator('body')).not.toContainText('{"error"');
	});
}

test('ERR_ACT is retried, then the round plays', async ({ page }) => {
	const plays = playRequests(page);
	await openGame(page, gameUrl(['act2']));
	await spin(page);
	await expect.poll(() => plays.length, { timeout: 20_000 }).toBe(3);
	expect(plays).toEqual([429, 429, 200]);
	expect(await errorText(page)).toBe('');
});

test('gameModes maxBet caps bet levels per mode', async ({ page }) => {
	await openGame(page, gameUrl(['maxbuy5']));
	expect(await sv<Record<string, number>>(page, 'sv.stateSession.modeMaxBet')).toMatchObject({
		...Object.fromEntries(BUY.map((k) => [k, 5])),
		[SPIN]: 100,
	});
	await sv(page, `(sv.stateBet.betAmount = 20, sv.stateBet.activeBetModeKey = '${BUY[0]}', true)`);
	await expect.poll(() => sv<number>(page, 'sv.stateBet.betAmount')).toBe(5);
	expect(await sv<number>(page, 'Math.max(...sv.stateConfig.betAmountOptions)')).toBe(5);
	await sv(page, `(sv.stateBet.activeBetModeKey = '${SPIN}', true)`);
	await expect.poll(() => sv<number>(page, 'Math.max(...sv.stateConfig.betAmountOptions)')).toBe(100);
});

test('bonus resume: /bet/event recorded, reload resumes the open round', async ({ page, request }) => {
	test.setTimeout(300_000);
	const url = gameUrl(['b5000']);
	const sessionID = new URL(url, 'https://x').searchParams.get('sessionID')!;
	const events: string[] = [];
	page.on('request', (r) => {
		if (r.url().includes('/rgs/bet/event')) events.push(JSON.parse(r.postData() || '{}').event);
	});
	await openGame(page, url);
	await request.post('https://localhost:3007/rgs/mock/force', { data: { sessionID, next: 'bonus' } });
	await spin(page);
	// The bonus intro waits for a press; keep pressing until free spins are being recorded.
	const canvas0 = page.locator('canvas').first();
	await expect
		.poll(
			async () => {
				await canvas0.click({ position: { x: 640, y: 360 } }).catch(() => undefined);
				return events.length;
			},
			{ timeout: 60_000, intervals: [1500] },
		)
		.toBeGreaterThan(1);

	// Reload mid-bonus: authenticate returns the open round with the last recorded event.
	const auth = page.waitForResponse((r) => r.url().includes('/rgs/wallet/authenticate'));
	let ended = false;
	page.on('request', (r) => {
		if (r.url().includes('/rgs/wallet/end-round')) ended = true;
	});
	await page.reload();
	const round = (await (await auth).json()).round;
	expect(round?.active).toBe(true);
	expect(Number(round.event)).toBeGreaterThan(0);
	// The server may have recorded one step more than this listener saw before the reload (owner-approved
	// fix 2026-11-07 for a timing race): it must be at least the last step the browser sent.
	expect(Number(round.event)).toBeGreaterThanOrEqual(Math.max(...events.map(Number)));
	// Resume plays the rest of the bonus and settles it.
	await page.waitForFunction(() => (globalThis as any).__sv, null, { timeout: 60_000 });
	const canvas = page.locator('canvas').first();
	// Press through loading screen, bonus intro and outro until the resumed round is settled.
	await expect
		.poll(
			async () => {
				await canvas.click({ position: { x: 640, y: 360 } }).catch(() => undefined);
				return ended;
			},
			{ timeout: 200_000, intervals: [1500] },
		)
		.toBe(true);
	expect(await errorText(page)).toBe('');
});

test('social=true forces English', async ({ page }) => {
	const auth = page.waitForRequest((r) => r.url().includes('/rgs/wallet/authenticate'));
	await page.goto(gameUrl(['social'], '&social=true').replace('lang=en', 'lang=de'));
	expect(JSON.parse((await auth).postData() || '{}').language).toBe('en');
});

test('malformed request gets plain-text 400 from the mock (RGS parity)', async ({ request }) => {
	const res = await request.post('https://localhost:3007/rgs/wallet/authenticate', { data: Buffer.from('{bad'), headers: { 'content-type': 'application/json' } });
	expect(res.status()).toBe(400);
	expect(await res.text()).toBe('Bad Request');
});

test('prefers-reduced-motion starts in turbo', async ({ page }) => {
	await page.emulateMedia({ reducedMotion: 'reduce' });
	await openGame(page, gameUrl());
	expect(await sv<boolean>(page, 'sv.stateBet.isTurbo')).toBe(true);
});

test('prefers-reduced-motion keeps turbo off when the jurisdiction disables turbo', async ({ page }) => {
	await page.emulateMedia({ reducedMotion: 'reduce' });
	await openGame(page, gameUrl(['noturbo']));
	expect(await sv<boolean>(page, 'sv.stateBet.isTurbo')).toBe(false);
});
