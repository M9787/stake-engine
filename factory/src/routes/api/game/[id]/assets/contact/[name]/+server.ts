// GET /api/game/[id]/assets/contact/[name] -> build/<id>/contact_<land|port|all>.png
import fs from 'node:fs';
import path from 'node:path';

import { error } from '@sveltejs/kit';

import { buildDir, skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
	if (!['land', 'port', 'all'].includes(params.name)) error(404, 'contact sheet name must be land, port or all');
	try {
		skinOf(params.id);
	} catch (e) {
		error(404, (e as Error).message);
	}
	const file = path.join(buildDir(params.id), `contact_${params.name}.png`);
	if (!fs.existsSync(file)) error(404, 'No contact sheet yet: press "Contact sheet" first.');
	return new Response(await fs.promises.readFile(file), { headers: { 'content-type': 'image/png', 'cache-control': 'no-store' } });
};
