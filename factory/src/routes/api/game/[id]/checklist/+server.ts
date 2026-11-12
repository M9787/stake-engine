// GET /api/game/[id]/checklist -> StakeChecklist from build/<id>/reports/stake_checklist.json
// (tools/release/checklist.py). No checklist yet -> 404 with a plain message.
import fs from 'node:fs';
import path from 'node:path';

import { error, json } from '@sveltejs/kit';

import { buildDir, readJson, skinOf } from '$lib/server/repo';
import type { StakeChecklist } from '$lib/types';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
	try {
		skinOf(params.id);
	} catch (e) {
		error(404, (e as Error).message);
	}
	const file = path.join(buildDir(params.id), 'reports', 'stake_checklist.json');
	if (!fs.existsSync(file)) error(404, 'No Stake checklist yet: press "Run checklist" first.');
	try {
		return json(readJson<StakeChecklist>(file), { headers: { 'cache-control': 'no-store' } });
	} catch {
		error(500, 'stake_checklist.json could not be read: run the checklist again.');
	}
};
