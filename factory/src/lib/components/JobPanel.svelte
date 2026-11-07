<script module lang="ts">
	import type { Job, ToolId } from '$lib/types';

	/** Client copy of the tool labels and typical minutes (src/lib/server/tools.ts is server-only). */
	export const TOOL_INFO: Record<ToolId, { label: string; minutes: number }> = {
		sync: { label: 'Sync core + skin', minutes: 1 },
		prompts: { label: 'Render prompts', minutes: 0.2 },
		check_art_in: { label: 'Check art files', minutes: 0.2 },
		ingest_all: { label: 'Ingest all files', minutes: 3 },
		ingest_slot: { label: 'Ingest slot', minutes: 0.5 },
		contact_sheet: { label: 'Contact sheet', minutes: 0.5 },
		sign_off: { label: 'Sign off art', minutes: 0.5 },
		audio: { label: 'Build audio sprite', minutes: 1 },
		math_preview: { label: 'Math preview (estimate)', minutes: 3 },
		math_candidate: { label: 'Math candidate (full)', minutes: 40 },
		fe_config: { label: 'Math -> web config', minutes: 0.2 },
		mock: { label: 'Preview data', minutes: 1 },
		web_build: { label: 'Build web', minutes: 1 },
		gate_fast: { label: 'Check (fast)', minutes: 8 },
		gate_full: { label: 'Check (full)', minutes: 45 },
		package: { label: 'Package for Stake', minutes: 3 },
		preview_server: { label: 'Start game preview', minutes: 0.5 },
		test_assets: { label: 'Fill empty slots with test assets', minutes: 2 },
		clear_test_assets: { label: 'Remove test assets', minutes: 0.5 },
		apply_preset: { label: 'Apply preset', minutes: 0.2 },
		math_freeze: { label: 'Freeze math', minutes: 0.2 },
		event_ids: { label: 'Pick reviewer event IDs', minutes: 1 },
		shots: { label: 'Screenshots', minutes: 2 },
		pack: { label: 'Submission pack', minutes: 1 },
	};

	/** Turn a failed response into one plain sentence. */
	export async function errorText(res: Response): Promise<string> {
		let detail = '';
		try {
			const body = await res.clone().json();
			detail = body?.message ?? body?.error ?? body?.plain ?? '';
		} catch {
			try {
				const t = (await res.text()).trim();
				detail = t.startsWith('<') ? '' : t.slice(0, 300); // never show an HTML error page
			} catch {
				/* ignore */
			}
		}
		if (res.status === 404 && !detail) return 'This part of the editor is not available yet (the server answered "not found").';
		return detail ? String(detail) : `The editor server answered with an error (code ${res.status}).`;
	}

	/** fetch + JSON with plain-language errors. Throws Error(message). */
	export async function api<T>(url: string, init?: RequestInit): Promise<T> {
		let res: Response;
		try {
			res = await fetch(url, init);
		} catch {
			throw new Error('The editor server did not answer. Is it still running?');
		}
		if (!res.ok) throw new Error(await errorText(res));
		return (await res.json()) as T;
	}

	export const sendJson = (method: string, body: unknown): RequestInit => ({
		method,
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify(body),
	});

	export const fmtDuration = (ms: number) => {
		const s = Math.max(0, Math.round(ms / 1000));
		return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`;
	};

	export const fmtMinutes = (m: number) => (m < 1 ? `${Math.round(m * 60)} s` : `${m} min`);

	export const STATUS_TEXT: Record<string, string> = {
		running: 'Running',
		done: 'Finished',
		failed: 'Failed',
		cancelled: 'Cancelled',
	};
</script>

<script lang="ts">
	import { onDestroy } from 'svelte';

	type Props = {
		game: string;
		tool: ToolId;
		opts?: import('$lib/types').JobOpts;
		label?: string;
		confirm?: string;
		ondone?: (job: Job) => void;
		/** Optional: called on every status update (start, poll). */
		onchange?: (job: Job) => void;
		/** Optional: id of an already started job to show and follow. */
		attach?: string;
		/** Optional: disable the start button (with the reason shown next to it). */
		disabled?: boolean;
		disabledNote?: string;
	};
	let { game, tool, opts, label, confirm, ondone, onchange, attach, disabled = false, disabledNote }: Props = $props();

	const info = $derived(TOOL_INFO[tool]);
	let job = $state<Job | null>(null);
	let log = $state('');
	let error = $state('');
	let starting = $state(false);
	let now = $state(Date.now());
	let next = 0;
	let timer: ReturnType<typeof setTimeout> | null = null;
	let ticker: ReturnType<typeof setInterval> | null = null;
	let logBox = $state<HTMLPreElement | null>(null);
	let destroyed = false;
	let attachedId = '';

	const running = $derived(job?.status === 'running');
	const elapsed = $derived(job ? (job.ended ? Date.parse(job.ended) : now) - Date.parse(job.started) : 0);
	const overTime = $derived(running && info && elapsed > info.minutes * 60_000 * 2);

	function stopTimers() {
		if (timer) clearTimeout(timer);
		if (ticker) clearInterval(ticker);
		timer = null;
		ticker = null;
	}

	function follow(j: Job) {
		stopTimers();
		job = j;
		log = '';
		next = 0;
		error = '';
		onchange?.(j);
		ticker = setInterval(() => (now = Date.now()), 1000);
		poll();
	}

	async function poll() {
		if (!job || destroyed) return;
		const id = job.id;
		try {
			const r = await api<{ job: Job; log: string; next: number }>(`/api/jobs/${encodeURIComponent(id)}?from=${next}`);
			if (destroyed || job?.id !== id) return;
			const atBottom = !logBox || logBox.scrollTop + logBox.clientHeight >= logBox.scrollHeight - 20;
			if (r.log) log += r.log;
			next = r.next;
			const was = job.status;
			job = r.job;
			if (r.job.status !== was || r.log) onchange?.(r.job);
			if (atBottom && logBox) queueMicrotask(() => logBox && (logBox.scrollTop = logBox.scrollHeight));
			if (r.job.status !== 'running') {
				stopTimers();
				ondone?.(r.job);
				return;
			}
		} catch (e) {
			error = (e as Error).message;
		}
		timer = setTimeout(poll, 700);
	}

	async function start() {
		if (confirm && !window.confirm(confirm)) return;
		starting = true;
		error = '';
		try {
			const j = await api<Job>(`/api/game/${encodeURIComponent(game)}/jobs`, sendJson('POST', { tool, ...(opts ? { opts } : {}) }));
			follow(j);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			starting = false;
		}
	}

	async function cancel() {
		if (!job) return;
		try {
			const j = await api<Job>(`/api/jobs/${encodeURIComponent(job.id)}/cancel`, { method: 'POST' });
			job = j;
			onchange?.(j);
		} catch (e) {
			error = (e as Error).message;
		}
	}

	$effect(() => {
		if (attach && attach !== attachedId && attach !== job?.id) {
			attachedId = attach;
			api<{ job: Job; log: string; next: number }>(`/api/jobs/${encodeURIComponent(attach)}?from=0`)
				.then((r) => follow(r.job))
				.catch((e) => (error = (e as Error).message));
		}
	});

	onDestroy(() => {
		destroyed = true;
		stopTimers();
	});
</script>

<div class="job panel">
	<div class="row">
		<button onclick={start} disabled={disabled || starting || running} aria-label={label ?? info?.label ?? tool}>
			{starting ? 'Starting…' : (label ?? info?.label ?? tool)}
		</button>
		{#if running}
			<button class="secondary" onclick={cancel}>Cancel</button>
		{/if}
		{#if job}
			<span class="status {job.status}" role="status">{STATUS_TEXT[job.status] ?? job.status}</span>
			<span class="muted">
				{fmtDuration(elapsed)}{#if info} of about {fmtMinutes(info.minutes)}{/if}
			</span>
		{:else if disabled && disabledNote}
			<span class="muted">{disabledNote}</span>
		{:else if info}
			<span class="muted">Usually takes about {fmtMinutes(info.minutes)}.</span>
		{/if}
	</div>

	{#if overTime}
		<p class="warn small">This is taking longer than usual. You can keep waiting or press Cancel.</p>
	{/if}

	{#if error}
		<div class="errbox" role="alert">{error}</div>
	{/if}

	{#if job?.status === 'failed'}
		<div class="errbox" role="alert">
			<strong>It did not work.</strong>
			{job.plain ?? 'The step stopped with an error. The details are in the log below.'}
		</div>
	{/if}

	{#if job}
		<details open={running || job.status === 'failed'}>
			<summary class="muted">Details (log)</summary>
			<pre class="log" bind:this={logBox} aria-label="Job log">{log || (running ? 'Waiting for output…' : '(no output)')}</pre>
		</details>
	{/if}
</div>

<style>
	.job { display: flex; flex-direction: column; gap: 8px; }
	.row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
	.status { font-weight: 700; padding: 2px 8px; border-radius: 10px; background: #0f0d18; border: 1px solid var(--line); }
	.status.running { color: var(--accent); }
	.status.done { color: var(--ok); }
	.status.failed { color: var(--bad); }
	.status.cancelled { color: var(--muted); }
	.errbox { background: #3a1714; border: 1px solid var(--bad); color: #ffd9d4; border-radius: 6px; padding: 8px 10px; white-space: pre-wrap; }
	.small { margin: 0; font-size: 13px; }
	details pre { margin: 6px 0 0; }
	summary { cursor: pointer; }
</style>
