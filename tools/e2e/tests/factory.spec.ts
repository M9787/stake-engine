// M12 exit (docs/10 plan v3.3 section 13): the factory editor proven end to end on 3 asset slots.
// Needs the editor running: factory\start.cmd (or `Push-Location factory; pnpm exec vite dev`).
// Run: $env:FACTORY='1'; Push-Location tools\e2e; pnpm exec playwright test factory; Pop-Location
// Leaves zz_smoke with 3 ingested slots; tools\e2e\factory_cleanup.ps1 removes them.
import fs from 'node:fs';
import path from 'node:path';
import { expect, test } from '@playwright/test';

const EDITOR = 'http://127.0.0.1:5174';
const GAME = 'zz_smoke';
const SLOTS = ['symbol.H1', 'symbol.H2', 'symbol.S'];
const FIXTURES = path.resolve(import.meta.dirname, '../../../build/factory_test');

test.skip(!process.env.FACTORY, 'set FACTORY=1 with the editor running on 127.0.0.1:5174');
test.describe.configure({ mode: 'serial' });

const headers = { Origin: EDITOR };

test('home lists the games and the computer check passes', async ({ page, request }) => {
	const games = await (await request.get(`${EDITOR}/api/games`)).json();
	expect(games.map((g: { id: string }) => g.id)).toEqual(expect.arrayContaining(['seventh_veil', GAME]));
	const doctor = await (await request.get(`${EDITOR}/api/doctor`)).json();
	expect(doctor.filter((r: { status: string }) => r.status === 'FAIL')).toEqual([]);
	await page.goto(EDITOR);
	await expect(page.getByText('Smoke Probe').first()).toBeVisible();
});

test('asset desk: upload raw + edited, provenance, ingest 3 slots', async ({ page, request }) => {
	test.setTimeout(240_000);
	for (const slot of SLOTS) {
		for (const lane of ['raw', 'edited']) {
			const file = path.join(FIXTURES, `${slot}.${lane}.png`);
			const r = await request.post(`${EDITOR}/api/game/${GAME}/assets/upload`, {
				headers,
				multipart: { slot, lane, file: { name: `${slot}.png`, mimeType: 'image/png', buffer: fs.readFileSync(file) } },
			});
			expect(r.status(), await r.text()).toBe(200);
		}
		const p = await request.put(`${EDITOR}/api/game/${GAME}/assets/provenance`, {
			headers,
			data: { slot, licence: 'midjourney-pro', sourceUrl: 'https://example.com/job', editNote: 'recoloured and cleaned edges' },
		});
		expect(p.status(), await p.text()).toBe(200);
		const job = await (await request.post(`${EDITOR}/api/game/${GAME}/jobs`, { headers, data: { tool: 'ingest_slot', opts: { slot } } })).json();
		await expect
			.poll(async () => (await (await request.get(`${EDITOR}/api/jobs/${job.id}`)).json()).job.status, { timeout: 120_000 })
			.toBe('done');
	}
	const desk = await (await request.get(`${EDITOR}/api/game/${GAME}/assets`)).json();
	for (const slot of SLOTS) {
		const card = desk.slots.find((s: { id: string }) => s.id === slot);
		expect(card.ingested, slot).toBe(true);
		expect(card.complete, `${slot}: ${card.issues.join('; ')}`).toBe(true);
	}
	await page.goto(`${EDITOR}/game/${GAME}/assets`);
	await expect(page.getByText('symbol.H1').first()).toBeVisible();
});

test('pages render without errors', async ({ page }) => {
	const errors: string[] = [];
	page.on('pageerror', (e) => errors.push(e.message));
	for (const p of ['', '/assets', '/build', '/preview']) {
		await page.goto(`${EDITOR}/game/${GAME}${p}`);
		await page.waitForLoadState('networkidle');
	}
	expect(errors).toEqual([]);
});
