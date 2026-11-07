// PUT {sref: string|null}: set the Midjourney style reference (the picked hero image URL) in
// skins/<skin>/assets.json style.sref. Targeted edit when the key exists, so a hand-formatted file keeps
// its layout; otherwise the key is added to the style block.
import fs from 'node:fs';
import path from 'node:path';
import { json } from '@sveltejs/kit';

import { skinOf } from '$lib/server/repo';
import { snapshot } from '$lib/server/history';

const URL_RE = /^https:\/\/[^\s"'<>\\]{8,400}$/;
const fail = (status: number, message: string) => json({ error: message }, { status });

export const PUT = async ({ params, request }) => {
	const skin = skinOf(params.id);
	const body = await request.json().catch(() => ({}));
	const sref: string | null = body.sref ? String(body.sref).trim() : null;
	if (sref !== null && !URL_RE.test(sref))
		return fail(400, 'Paste the full https:// link of the hero image (Midjourney: right-click the image, Copy image address).');
	const file = path.join(skin.dir, 'assets.json');
	if (!fs.existsSync(file)) return fail(404, 'This game has no assets.json style bible.');
	const text = fs.readFileSync(file, 'utf-8');
	const re = /("sref"\s*:\s*)(null|"[^"]*")/;
	let updated: string;
	if (re.test(text)) {
		updated = text.replace(re, `$1${sref === null ? 'null' : JSON.stringify(sref)}`);
	} else {
		const data = JSON.parse(text);
		data.style = { ...(data.style ?? {}), sref };
		updated = JSON.stringify(data, null, 2) + '\n';
	}
	JSON.parse(updated); // never write a broken file
	if (updated !== text) {
		snapshot(skin.dir);
		fs.writeFileSync(file, updated, 'utf-8');
	}
	return json({ sref });
};
