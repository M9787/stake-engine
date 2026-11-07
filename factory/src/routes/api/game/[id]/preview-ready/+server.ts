// GET /api/game/[id]/preview-ready -> { skin, mock, running }
//   skin: build/<id>/web/skin.generated.ts exists (written by sync once math output exists)
//   mock: web-sdk/apps/cluster-tumble/.mock-rgs/<id>/ exists (scripts/books_to_mock.py)
//   running: the preview server (port 3007, one for all games) that is running now, or null
import fs from 'node:fs';
import path from 'node:path';
import { json } from '@sveltejs/kit';

import { listJobs, reconcile } from '$lib/server/jobs';
import { buildDir, listSkins, ROOT, skinOf } from '$lib/server/repo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params }) => {
	const { id } = skinOf(params.id);
	const skin = fs.existsSync(path.join(buildDir(id), 'web', 'skin.generated.ts'));
	const mock = fs.existsSync(path.join(ROOT, 'web-sdk', 'apps', 'cluster-tumble', '.mock-rgs', id));
	let running: { game: string; jobId: string } | null = null;
	for (const s of listSkins()) {
		reconcile(s.id); // a "running" job left by an earlier editor session is not running
		const live = listJobs(s.id).find((j) => j.tool === 'preview_server' && j.status === 'running');
		if (live) {
			running = { game: s.id, jobId: live.id };
			if (s.id !== id) break; // another game holds the port: that is what the page must show
		}
	}
	return json({ skin, mock, running });
};
