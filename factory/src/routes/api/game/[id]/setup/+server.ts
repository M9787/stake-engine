// GET /api/game/[id]/setup -> current mechanics + math (lib/server/setup.ts readSetup)
// PUT {section, ...form} -> { validation, snapshot } | 400 { error }   (section: symbols|paytable|modes|features|math|review)
// Every save snapshots the skin first (history.ts), then validate.py --json.
import { json } from '@sveltejs/kit';

import { isRefusal, readSetup, saveSection } from '$lib/server/setup';
import { skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params }) => json(readSetup(skinOf(params.id)));

export const PUT: RequestHandler = async ({ params, request }) => {
	const s = skinOf(params.id);
	let body: any;
	try {
		body = await request.json();
	} catch {
		return json({ error: 'body must be JSON {section, ...}' }, { status: 400 });
	}
	try {
		return json(await saveSection(s, String(body?.section ?? ''), body));
	} catch (e: any) {
		return json({ error: e.message }, { status: isRefusal(e) ? 400 : 500 });
	}
};
