// PUT /api/game/[id]/assets/provenance {slot, licence?, sourceUrl?, editNote?, redo?} -> SlotCard
// Desk extra: {sitting, minutes} logs owner minutes for a sitting -> {ok: true}
import { error, json } from '@sveltejs/kit';

import { cardOf, saveProvenance, statusOf, type ProvenanceInput } from '$lib/server/assets';
import { isSlotId } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const PUT: RequestHandler = async ({ params, request }) => {
	let body: ProvenanceInput;
	try {
		body = await request.json();
	} catch {
		error(400, 'Send the provenance line as JSON.');
	}
	if (!body || typeof body !== 'object') error(400, 'Send the provenance line as JSON.');
	if (body.slot !== undefined && (typeof body.slot !== 'string' || !isSlotId(body.slot))) error(400, 'invalid slot id');
	try {
		await saveProvenance(params.id, body);
		return json(body.slot ? await cardOf(params.id, body.slot) : { ok: true });
	} catch (e) {
		error(statusOf(e), (e as Error).message);
	}
};
