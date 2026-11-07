// POST /api/game/[id]/setup/preset {preset: PresetRequest} -> { job, snapshot } | 400 { error }
// Snapshots the skin, then starts the whitelisted apply_preset job (tools/gamedef/apply_preset.py).
import { json } from '@sveltejs/kit';

import { isRefusal, startPreset } from '$lib/server/setup';
import { skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ params, request }) => {
	const s = skinOf(params.id);
	let body: any;
	try {
		body = await request.json();
	} catch {
		return json({ error: 'body must be JSON {preset}' }, { status: 400 });
	}
	try {
		return json(startPreset(s, body?.preset));
	} catch (e: any) {
		return json({ error: e.message }, { status: isRefusal(e) ? 400 : 409 });
	}
};
