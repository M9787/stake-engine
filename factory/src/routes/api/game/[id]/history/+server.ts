// GET /api/game/[id]/history -> { ts, files }[] (newest first)
// POST { restore: ts } -> { restored, backup, validation } | 400 { error }
import { json } from '@sveltejs/kit';

import { validate } from '$lib/server/games';
import { list, restore } from '$lib/server/history';
import { skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params }) => json(list(skinOf(params.id).dir));

export const POST: RequestHandler = async ({ params, request }) => {
	const s = skinOf(params.id);
	let body: any;
	try {
		body = await request.json();
	} catch {
		body = null;
	}
	if (typeof body?.restore !== 'string') return json({ error: 'body must be JSON {restore: "<snapshot id>"}' }, { status: 400 });
	try {
		const r = restore(s.dir, body.restore);
		return json({ ...r, validation: await validate(s) });
	} catch (e: any) {
		return json({ error: e.message }, { status: 400 });
	}
};
