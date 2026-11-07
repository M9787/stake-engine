// GET /api/game/[id]/pack -> PackSummary from build/<id>/pack/pack.json (tools/release/pack.py).
// No pack yet -> 404 with a plain message (the Submit page shows it as "not built yet").
import fs from 'node:fs';
import path from 'node:path';

import { error, json } from '@sveltejs/kit';

import { buildDir, readJson, skinOf } from '$lib/server/repo';
import type { PackSummary } from '$lib/types';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
	try {
		skinOf(params.id);
	} catch (e) {
		error(404, (e as Error).message);
	}
	const file = path.join(buildDir(params.id), 'pack', 'pack.json');
	if (!fs.existsSync(file)) error(404, 'No submission pack yet: press "Build submission pack" first.');
	try {
		const p = readJson<PackSummary>(file);
		return json(p, { headers: { 'cache-control': 'no-store' } });
	} catch {
		error(500, 'pack.json could not be read: build the submission pack again.');
	}
};
