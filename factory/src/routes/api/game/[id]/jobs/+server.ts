// GET /api/game/[id]/jobs -> Job[] (newest first) ; POST StartJob -> Job | 400 { error }
import { json } from '@sveltejs/kit';

import type { StartJob } from '$lib/types';
import { listJobs, reconcile, startJob } from '$lib/server/jobs';
import { skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params }) => {
	const { id } = skinOf(params.id);
	reconcile(id);
	return json(listJobs(id));
};

export const POST: RequestHandler = async ({ params, request }) => {
	const { id } = skinOf(params.id);
	let body: StartJob;
	try {
		body = await request.json();
	} catch {
		return json({ error: 'body must be JSON {tool, opts?}' }, { status: 400 });
	}
	if (!body || typeof body.tool !== 'string') return json({ error: 'body must be JSON {tool, opts?}' }, { status: 400 });
	const opts = body.opts ?? {};
	// Values are validated in startJob (src/lib/server/jobs.ts).
	const OPT_KEYS = ['slot', 'signer', 'version', 'preset'];
	if (typeof opts !== 'object' || Array.isArray(opts) || Object.keys(opts).some((k) => !OPT_KEYS.includes(k)))
		return json({ error: 'opts may only hold slot, signer, version and preset' }, { status: 400 });
	if (body.tool === 'ingest_slot' && typeof opts.slot !== 'string') return json({ error: 'pick a slot to ingest' }, { status: 400 });
	if (body.tool === 'sign_off' && typeof opts.signer !== 'string') return json({ error: 'enter the name of the person signing' }, { status: 400 });
	try {
		return json(startJob(id, body.tool, { slot: opts.slot, signer: opts.signer, version: opts.version, preset: opts.preset }));
	} catch (e: any) {
		return json({ error: e.message }, { status: 400 });
	}
};
