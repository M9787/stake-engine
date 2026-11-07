// POST /api/jobs/[jobId]/cancel -> Job (a job that is not running is returned unchanged)
import { json } from '@sveltejs/kit';

import { cancelJob } from '$lib/server/jobs';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = ({ params }) => {
	const job = cancelJob(params.jobId);
	if (!job) return json({ error: `unknown job '${params.jobId}'` }, { status: 404 });
	return json(job);
};
