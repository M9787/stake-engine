// GET /api/game/[id]/pack/file?name=<path> -> one file of the submission pack.
// Serves only names listed in pack.json "files"; looks in build/<id>/pack first, then build/<id>/shots
// for "shots/<file>" names. No other path can be read.
import fs from 'node:fs';
import path from 'node:path';

import { error } from '@sveltejs/kit';

import { buildDir, inside, readJson, skinOf } from '$lib/server/repo';
import type { PackSummary } from '$lib/types';
import type { RequestHandler } from './$types';

const TYPES: Record<string, string> = {
	'.html': 'text/html; charset=utf-8',
	'.md': 'text/markdown; charset=utf-8',
	'.json': 'application/json; charset=utf-8',
	'.png': 'image/png',
};

export const GET: RequestHandler = async ({ params, url }) => {
	const name = url.searchParams.get('name') ?? '';
	try {
		skinOf(params.id);
	} catch (e) {
		error(404, (e as Error).message);
	}
	const packDir = path.join(buildDir(params.id), 'pack');
	const listFile = path.join(packDir, 'pack.json');
	if (!fs.existsSync(listFile)) error(404, 'No submission pack yet: press "Build submission pack" first.');
	const pack = readJson<PackSummary>(listFile);
	if (!name || !pack.files.some((f) => f.path === name)) error(404, `'${name}' is not a file of this pack`);
	const type = TYPES[path.extname(name).toLowerCase()];
	if (!type) error(404, 'file type not served');
	const candidates: string[] = [];
	try {
		candidates.push(inside(packDir, name));
		if (name.startsWith('shots/')) candidates.push(inside(path.join(buildDir(params.id), 'shots'), name.slice('shots/'.length)));
	} catch (e) {
		error(400, (e as Error).message);
	}
	const file = candidates.find((c) => fs.existsSync(c) && fs.statSync(c).isFile());
	if (!file) error(404, `'${name}' is listed but missing on disk: build the submission pack again.`);
	return new Response(await fs.promises.readFile(file), {
		headers: { 'content-type': type, 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' },
	});
};
