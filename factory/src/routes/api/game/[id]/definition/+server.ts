// GET /api/game/[id]/definition -> Definition ; PUT Definition -> { validation, snapshot } | 400 { error }
// PUT snapshots the skin (history.ts) before writing; snapshot is null when nothing changed.
import { json } from '@sveltejs/kit';

import { readDefinition, writeDefinition } from '$lib/server/games';
import { skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params }) => json(readDefinition(skinOf(params.id)));

export const PUT: RequestHandler = async ({ params, request }) => {
	const s = skinOf(params.id);
	let body: any;
	try {
		body = await request.json();
	} catch {
		return json({ error: 'body must be a JSON Definition' }, { status: 400 });
	}
	try {
		return json(await writeDefinition(s, body));
	} catch (e: any) {
		return json({ error: e.message }, { status: 400 });
	}
};
