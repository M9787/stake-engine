// GET /api/games -> GameSummary[] ; POST /api/games (NewGameRequest) -> { id, validation } | 400 { error }
// New games are made only by tools/new_game.py (one code path).
import { execFile } from 'node:child_process';
import path from 'node:path';
import { promisify } from 'node:util';
import { json } from '@sveltejs/kit';

import type { NewGameRequest } from '$lib/types';
import { summaries } from '$lib/server/games';
import { PY, ROOT, isGameId, listSkins } from '$lib/server/repo';
import type { RequestHandler } from './$types';

const run = promisify(execFile);

export const GET: RequestHandler = () => json(summaries());

export const POST: RequestHandler = async ({ request }) => {
	let body: NewGameRequest;
	try {
		body = await request.json();
	} catch {
		return json({ error: 'body must be JSON {template, id, displayName}' }, { status: 400 });
	}
	const { template, id, displayName } = body ?? ({} as NewGameRequest);
	if (typeof template !== 'string' || !listSkins().some((s) => s.skin === template))
		return json({ error: `template '${template}' is not a skin folder` }, { status: 400 });
	if (typeof id !== 'string' || !isGameId(id))
		return json({ error: 'game id: 3-32 characters, lower case letters, digits and _, starting with a letter' }, { status: 400 });
	if (typeof displayName !== 'string' || displayName.trim().length < 2 || displayName.trim().length > 40)
		return json({ error: 'display name: 2-40 characters' }, { status: 400 });
	const args = [path.join(ROOT, 'tools', 'new_game.py'), '--from', template, '--id', id, '--name', displayName.trim(), '--json'];
	let stdout = '';
	let stderr = '';
	try {
		({ stdout, stderr } = await run(PY, args, { cwd: ROOT, windowsHide: true, timeout: 120_000, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }));
	} catch (e: any) {
		stdout = e.stdout ?? '';
		stderr = e.stderr ?? e.message;
	}
	let r: any;
	try {
		r = JSON.parse(stdout.trim().split(/\r?\n/).pop() ?? '');
	} catch {
		return json({ error: `new_game.py did not answer: ${(stderr || stdout).trim().slice(0, 500)}` }, { status: 400 });
	}
	if (!r.ok) return json({ error: r.error ?? 'new_game.py failed' }, { status: 400 });
	return json({ id: r.id, validation: r.validation });
};
