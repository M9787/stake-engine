// GET /api/doctor -> DoctorRow[] : scripts/doctor.ps1 (read-only) parsed from its table; cached 60 s.
import { execFile } from 'node:child_process';
import path from 'node:path';
import { promisify } from 'node:util';
import { json } from '@sveltejs/kit';

import type { DoctorRow } from '$lib/types';
import { ROOT } from '$lib/server/repo';
import type { RequestHandler } from './$types';

const run = promisify(execFile);
let cache: { at: number; rows: DoctorRow[] } | null = null;

/** Parse the Format-Table block: column starts come from the dashes line under the header. */
const parseTable = (out: string): DoctorRow[] => {
	const lines = out.split(/\r?\n/);
	const h = lines.findIndex((l, i) => /^\s*Tool\s+Want\s+Have\s+Status\s+Fix\s*$/.test(l) && /^[\s-]+$/.test(lines[i + 1] ?? ''));
	if (h < 0) return [];
	const starts = [...lines[h + 1].matchAll(/-+/g)].map((m) => m.index ?? 0);
	const rows: DoctorRow[] = [];
	for (const line of lines.slice(h + 2)) {
		if (!line.trim()) break;
		const cell = (i: number) => line.slice(starts[i], i + 1 < starts.length ? starts[i + 1] : undefined).trim();
		const status = cell(3);
		rows.push({
			tool: cell(0),
			want: cell(1),
			have: cell(2),
			status: (['PASS', 'WARN', 'FAIL'].includes(status) ? status : 'FAIL') as DoctorRow['status'],
			fix: cell(4),
		});
	}
	return rows;
};

export const GET: RequestHandler = async () => {
	if (cache && Date.now() - cache.at < 60_000) return json(cache.rows);
	const args = ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(ROOT, 'scripts', 'doctor.ps1')];
	let stdout = '';
	try {
		({ stdout } = await run('powershell.exe', args, { cwd: ROOT, windowsHide: true, timeout: 60_000 }));
	} catch (e: any) {
		stdout = e.stdout ?? ''; // exit 1 = a required check failed; the table is still printed
	}
	const rows = parseTable(stdout);
	if (!rows.length) return json({ error: 'doctor.ps1 printed no table', output: stdout.slice(0, 2000) }, { status: 500 });
	cache = { at: Date.now(), rows };
	return json(rows);
};
