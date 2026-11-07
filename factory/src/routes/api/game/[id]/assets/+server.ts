// GET /api/game/[id]/assets -> AssetDesk (+ desk extras, see src/lib/server/assets.ts Desk)
import { error, json } from '@sveltejs/kit';

import { buildDesk, statusOf } from '$lib/server/assets';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
	try {
		return json(await buildDesk(params.id));
	} catch (e) {
		error(statusOf(e), (e as Error).message);
	}
};
