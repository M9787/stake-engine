// GET /api/game/[id]/setup/strip/[strip] -> the reel strip CSV (download)
// PUT (body: CSV text) -> { validation, snapshot } | 400 { error }   one row per stop, one column per reel
import { json } from '@sveltejs/kit';

import { isRefusal, readStrip, writeStrip } from '$lib/server/setup';
import { skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params }) => {
	try {
		const { name, text } = readStrip(skinOf(params.id), params.strip);
		return new Response(text, { headers: { 'content-type': 'text/csv; charset=utf-8', 'content-disposition': `attachment; filename="${name}"` } });
	} catch (e: any) {
		return json({ error: e.message }, { status: 404 });
	}
};

export const PUT: RequestHandler = async ({ params, request }) => {
	const s = skinOf(params.id);
	try {
		return json(await writeStrip(s, params.strip, await request.text()));
	} catch (e: any) {
		return json({ error: e.message }, { status: isRefusal(e) ? 400 : 500 });
	}
};
