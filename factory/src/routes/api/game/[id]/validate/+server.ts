// GET /api/game/[id]/validate -> ValidateResult (tools/gamedef/validate.py --json)
import { json } from '@sveltejs/kit';

import { validate } from '$lib/server/games';
import { skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => json(await validate(skinOf(params.id)));
