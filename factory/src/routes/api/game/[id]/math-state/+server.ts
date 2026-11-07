// GET /api/game/[id]/math-state -> MathState (tier from run_meta.json, frozen lookups, stale vs build/<id>/math_stamp.json)
// POST {stamp: true} -> MathState   records the current math hash after a math job finished (build page)
import { json } from '@sveltejs/kit';

import { mathState, stampMath } from '$lib/server/setup';
import { skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params }) => json(mathState(skinOf(params.id)));

export const POST: RequestHandler = async ({ params, request }) => {
	const s = skinOf(params.id);
	let body: any;
	try {
		body = await request.json();
	} catch {
		body = null;
	}
	if (body?.stamp !== true) return json({ error: 'body must be JSON {stamp: true}' }, { status: 400 });
	return json(stampMath(s));
};
