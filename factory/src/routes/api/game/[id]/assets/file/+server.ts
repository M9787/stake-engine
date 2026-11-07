// GET /api/game/[id]/assets/file?slot=&lane=raw|edited|final -> the file's bytes (thumbnails, audio preview)
import fs from 'node:fs';
import path from 'node:path';

import { error } from '@sveltejs/kit';

import { CONTENT_TYPE, laneFile, statusOf } from '$lib/server/assets';
import { isSlotId } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params, url }) => {
	const slot = url.searchParams.get('slot') ?? '';
	const lane = url.searchParams.get('lane') ?? '';
	if (!isSlotId(slot)) error(400, 'invalid slot id');
	if (lane !== 'raw' && lane !== 'edited' && lane !== 'final') error(400, "lane must be 'raw', 'edited' or 'final'");
	let file: string | null;
	try {
		file = await laneFile(params.id, slot, lane);
	} catch (e) {
		error(statusOf(e), (e as Error).message);
	}
	if (!file) error(404, `no ${lane} file for ${slot}`);
	const body = await fs.promises.readFile(file);
	return new Response(body, {
		headers: {
			'content-type': CONTENT_TYPE[path.extname(file).toLowerCase()] ?? 'application/octet-stream',
			'cache-control': 'no-store',
			'x-content-type-options': 'nosniff',
		},
	});
};
