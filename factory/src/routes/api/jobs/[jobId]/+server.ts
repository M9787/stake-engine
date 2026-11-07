// GET /api/jobs/[jobId]?from=<byte> -> JobLog
import { json } from '@sveltejs/kit';

import type { JobLog } from '$lib/types';
import { getJob, readLog } from '$lib/server/jobs';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params, url }) => {
	const job = getJob(params.jobId);
	if (!job) return json({ error: `unknown job '${params.jobId}'` }, { status: 404 });
	const fromRaw = url.searchParams.get('from') ?? '0';
	if (!/^\d{1,15}$/.test(fromRaw)) return json({ error: 'from must be a byte offset (0 or more)' }, { status: 400 });
	const { log, next } = readLog(job, Number(fromRaw));
	return json({ job, log, next } satisfies JobLog);
};
