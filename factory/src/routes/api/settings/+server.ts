// GET /api/settings -> StudioSettings (defaults when factory/settings.json is missing)
// PUT /api/settings StudioSettings -> StudioSettings | 400 { error }
// Provider fields entered once on the home page; tools/new_game.py copies providerName/providerNumber into new
// games (Factory v3). Existing games are never changed by this file.
import fs from 'node:fs';
import path from 'node:path';
import { json } from '@sveltejs/kit';

import type { StudioSettings } from '$lib/types';
import { ROOT, readJson, writeJson } from '$lib/server/repo';
import type { RequestHandler } from './$types';

const FILE = path.join(ROOT, 'factory', 'settings.json');
const PROVIDER = /^[a-z0-9_]{1,40}$/; // core/schema/game-definition.v1.schema.json identity.providerName

const read = (): StudioSettings => {
	const d = { providerName: '', providerNumber: 0, teamName: '' };
	if (!fs.existsSync(FILE)) return d;
	try {
		const s = readJson(FILE);
		return {
			providerName: typeof s.providerName === 'string' ? s.providerName : d.providerName,
			providerNumber: Number.isInteger(s.providerNumber) ? s.providerNumber : d.providerNumber,
			teamName: typeof s.teamName === 'string' ? s.teamName : d.teamName,
		};
	} catch {
		return d;
	}
};

const check = (b: any): string | null => {
	if (!b || typeof b !== 'object' || Array.isArray(b)) return 'body must be JSON {providerName, providerNumber, teamName}';
	const extra = Object.keys(b).filter((k) => !['providerName', 'providerNumber', 'teamName'].includes(k));
	if (extra.length) return `unknown settings: ${extra.join(', ')}`;
	if (typeof b.providerName !== 'string' || !PROVIDER.test(b.providerName))
		return 'provider name: 1-40 small letters, digits and _ (as Stake shows it in the game id)';
	if (!Number.isInteger(b.providerNumber) || b.providerNumber < 0 || b.providerNumber > 1_000_000) return 'provider number: a whole number, 0 or more';
	if (typeof b.teamName !== 'string' || b.teamName.trim().length > 60) return 'team name: at most 60 characters';
	return null;
};

export const GET: RequestHandler = () => json(read());

export const PUT: RequestHandler = async ({ request }) => {
	let body: any;
	try {
		body = await request.json();
	} catch {
		return json({ error: 'body must be JSON {providerName, providerNumber, teamName}' }, { status: 400 });
	}
	const refusal = check(body);
	if (refusal) return json({ error: refusal }, { status: 400 });
	const next: StudioSettings = { providerName: body.providerName, providerNumber: body.providerNumber, teamName: body.teamName.trim() };
	writeJson(FILE, next);
	return json(next);
};
