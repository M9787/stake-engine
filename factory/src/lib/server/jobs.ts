// Job runner (plan v2.1 runtime + v3.3): every tool runs as a detached child process with its output in
// build/<game>/jobs/<jobId>.log and its state in <jobId>.json. One job per game at a time (except the
// preview service). Cancel = taskkill /T /F (the whole process tree). A failed job never touches the
// previous build: the tools themselves write their outputs only on success.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

import type { Job, JobOpts, ToolId } from '$lib/types';
import { buildDir, isSlotId } from './repo';
import { TOOLS, toolAllowed } from './tools';
import { explain } from './plain';

const pids = new Map<string, number>(); // jobId -> pid (this server process)

const jobsDir = (game: string) => path.join(buildDir(game), 'jobs');
const jobFile = (game: string, id: string) => path.join(jobsDir(game), `${id}.json`);
export const logFile = (game: string, id: string) => path.join(jobsDir(game), `${id}.log`);

const save = (job: Job) => fs.writeFileSync(jobFile(job.game, job.id), JSON.stringify(job, null, 2));

export const listJobs = (game: string): Job[] => {
	const dir = jobsDir(game);
	if (!fs.existsSync(dir)) return [];
	return fs
		.readdirSync(dir)
		.filter((f) => f.endsWith('.json'))
		.map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8')) as Job)
		.sort((a, b) => b.started.localeCompare(a.started));
};

export const getJob = (jobId: string): Job | null => {
	if (!/^[a-z][a-z0-9_]{2,31}-\d{17}$/.test(jobId)) return null; // no path traversal via the URL
	const game = jobId.slice(0, jobId.lastIndexOf('-'));
	const f = jobFile(game, jobId);
	return fs.existsSync(f) ? (JSON.parse(fs.readFileSync(f, 'utf-8')) as Job) : null;
};

/** Start a whitelisted tool for a game. Throws Error with a plain message when not allowed. */
export const startJob = (game: string, tool: ToolId, opts: JobOpts = {}): Job => {
	const refusal = toolAllowed(tool, game);
	if (refusal) throw new Error(refusal);
	if (opts.slot !== undefined && !isSlotId(opts.slot)) throw new Error('invalid slot id');
	if (opts.signer !== undefined && !/^[\p{L} .'-]{2,60}$/u.test(opts.signer)) throw new Error('invalid signer name');
	if (opts.version !== undefined && !/^\d{1,6}$/.test(opts.version)) throw new Error('invalid math version (a number)');
	if (opts.preset !== undefined) {
		const p = opts.preset;
		const ok =
			/^[5-8]x[5-8]$/.test(p.board) &&
			['low', 'medium', 'high'].includes(p.volatility) &&
			Number.isFinite(p.wincap) && p.wincap >= 100 && p.wincap <= 1_000_000 &&
			Number.isFinite(p.bonusOneIn) && p.bonusOneIn >= 20 && p.bonusOneIn <= 2000 &&
			Array.isArray(p.modes) && p.modes.length > 0 && p.modes.every((m) => ['base', 'ante', 'buy'].includes(m));
		if (!ok) throw new Error('invalid preset: board 5x5-8x8, volatility low/medium/high, max win 100-1,000,000, bonus 1 in 20-2000, modes base/ante/buy');
	}
	const spec = TOOLS[tool];
	if (!spec.service) {
		const busy = listJobs(game).find((j) => j.status === 'running' && !TOOLS[j.tool].service && pids.has(j.id));
		if (busy) throw new Error(`'${TOOLS[busy.tool].label}' is still running for this game; wait or cancel it.`);
	}
	fs.mkdirSync(jobsDir(game), { recursive: true });
	const id = `${game}-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 17)}`;
	const args = spec.args(game, opts);
	const extraEnv = typeof spec.env === 'function' ? spec.env(game) : (spec.env ?? {});
	const job: Job = { id, game, tool, args, status: 'running', exitCode: null, started: new Date().toISOString(), ended: null, plain: null };
	save(job);
	const out = fs.openSync(logFile(game, id), 'a');
	const child = spawn(spec.exe, args, {
		cwd: spec.cwd,
		env: { ...process.env, GAME: game, PYTHONIOENCODING: 'utf-8', ...extraEnv },
		// Windows PowerShell 5.1 needs a console: with DETACHED_PROCESS it exits 0 at once with no output
		// (seen 2026-11-07: sync "done" in 90 ms, empty log). Cancel uses taskkill /T, so it does not need detached.
		detached: !/powershell/i.test(spec.exe),
		windowsHide: true,
		stdio: ['ignore', out, out],
	});
	fs.closeSync(out); // the child holds its own handle; keeping ours leaked one fd per job
	if (child.pid) pids.set(id, child.pid);
	child.on('exit', (code) => {
		pids.delete(id);
		const current = getJob(id) ?? job;
		if (current.status === 'cancelled') return;
		current.status = code === 0 ? 'done' : 'failed';
		current.exitCode = code;
		current.ended = new Date().toISOString();
		if (code !== 0) current.plain = explain(tool, fs.readFileSync(logFile(game, id), 'utf-8'));
		save(current);
	});
	child.on('error', (err) => {
		pids.delete(id);
		fs.appendFileSync(logFile(game, id), `\n${err.message}\n`);
		save({ ...job, status: 'failed', ended: new Date().toISOString(), plain: `Could not start ${spec.label}: ${err.message}` });
	});
	return job;
};

/** Read the log from byte `from`; returns the new text and the next offset (for polling). */
export const readLog = (job: Job, from = 0) => {
	const f = logFile(job.game, job.id);
	if (!fs.existsSync(f)) return { log: '', next: from };
	const size = fs.statSync(f).size;
	if (from >= size) return { log: '', next: size };
	const fd = fs.openSync(f, 'r');
	const buf = Buffer.alloc(size - from);
	fs.readSync(fd, buf, 0, buf.length, from);
	fs.closeSync(fd);
	return { log: buf.toString('utf-8'), next: size };
};

export const cancelJob = (jobId: string): Job | null => {
	const job = getJob(jobId);
	if (!job || job.status !== 'running') return job;
	const pid = pids.get(jobId);
	if (pid) spawn('taskkill', ['/PID', String(pid), '/T', '/F'], { windowsHide: true });
	pids.delete(jobId);
	job.status = 'cancelled';
	job.ended = new Date().toISOString();
	save(job);
	return job;
};

/** Jobs marked running by an earlier editor session (no live process here) are reported as failed. */
export const reconcile = (game: string) => {
	for (const j of listJobs(game)) {
		if (j.status === 'running' && !pids.has(j.id)) {
			save({ ...j, status: 'failed', ended: j.ended ?? new Date().toISOString(), plain: 'The editor was restarted while this job ran.' });
		}
	}
};
