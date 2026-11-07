<script lang="ts">
	import { onDestroy } from 'svelte';
	import { page } from '$app/state';
	import type { GameSummary, Job, MathState, ToolId } from '$lib/types';
	import { api, errorText, fmtDuration, fmtMinutes, sendJson, STATUS_TEXT, TOOL_INFO } from '$lib/components/JobPanel.svelte';

	const id = $derived(page.params.id as string);

	let game = $state<GameSummary | null>(null);
	let jobs = $state<Job[] | null>(null);
	let jobsError = $state('');
	let math = $state<MathState | null>(null); // null = not known (endpoint missing or failed)
	let viewing = $state<{ job: Job; log: string; error: string } | null>(null);

	// the job this page is running or following now, with its live log
	let current = $state<Job | null>(null);
	let liveLog = $state('');
	let runError = $state('');
	let chain = $state<{ label: string; tools: ToolId[]; at: number } | null>(null);
	let cancelled = false;
	let destroyed = false;
	let now = $state(Date.now());
	const ticker = setInterval(() => (now = Date.now()), 1000);

	const MATH_TOOLS: ToolId[] = ['math_preview', 'math_candidate'];

	type Step = {
		n: number;
		title: string;
		what: string;
		tools: ToolId[]; // run one after the other ("combo"); the step's status is that of the last one
		button: string;
		confirm?: string;
		warn?: string;
		mathOnly?: boolean; // re-runs or locks the math: off for a game whose math is approved by hand (Oracle)
	};
	const STEPS: Step[] = [
		{ n: 1, title: 'Prepare', what: 'Copies your latest changes (texts, colours, art, game rules) into the game engine.', tools: ['sync'], button: 'Prepare' },
		{
			n: 2,
			title: 'Math estimate',
			what: 'A quick estimate of how the game pays (10,000 test spins, a few minutes). Good for tuning, never for release.',
			tools: ['math_preview'],
			button: 'Run math estimate',
			mathOnly: true,
		},
		{
			n: 3,
			title: 'Prepare again + preview data',
			what: 'Now that math exists: writes the rules and skin data for the game screen, then sample spins for the preview. Runs both, one after the other.',
			tools: ['sync', 'mock'],
			button: 'Prepare again + make preview data',
		},
		{ n: 4, title: 'Build web', what: 'Builds the playable game files.', tools: ['web_build'], button: 'Build web' },
		{ n: 5, title: 'Quick check', what: 'Runs the fast set of automatic checks (rules, math, screen tests). Takes several minutes.', tools: ['gate_fast'], button: 'Run quick check' },
		{
			n: 6,
			title: 'Final math',
			what: 'The real math: 100,000 test spins per mode and the full optimizer. About 40 minutes. If the math is frozen, it only re-plays the spins with the frozen weights.',
			tools: ['math_candidate'],
			button: 'Run final math',
			warn: 'Uses a lot of memory (RAM) for about 40 minutes. Close other big programs first, and do not run a check or build at the same time.',
			confirm: 'Start the final math now? It takes about 40 minutes and uses a lot of memory (RAM). Close other big programs first.',
			mathOnly: true,
		},
		{
			n: 7,
			title: 'Freeze math',
			what: 'Keeps the weights of the final math, so later runs give exactly the same game. Needs a final math run (not an estimate).',
			tools: ['math_freeze'],
			button: 'Freeze math',
			confirm: 'Freeze the math now? Later math runs will reuse these weights.',
			mathOnly: true,
		},
		{ n: 8, title: 'Full check', what: 'All automatic checks, including the long ones. About 45 minutes.', tools: ['gate_full'], button: 'Run full check' },
		{ n: 9, title: 'Documents', what: 'Writes the submission documents (what to fill in on Stake, screenshots list, reports).', tools: ['pack'], button: 'Make documents' },
		{
			n: 10,
			title: 'Package',
			what: 'Makes the upload package for Stake. Only do this when all checks above passed.',
			tools: ['package'],
			button: 'Make package',
			confirm: 'Make the Stake upload package now? Only do this after the checks passed.',
		},
	];

	const locked = $derived(!!game?.frozenModes); // Oracle: math approved and locked
	const byN = (n: number) => STEPS[n - 1];

	// last job per tool (newest first list)
	const lastByTool = $derived.by(() => {
		const m = new Map<string, Job>();
		for (const j of jobs ?? []) if (!m.has(j.tool)) m.set(j.tool, j);
		return m;
	});
	const doneTool = (t: ToolId) => lastByTool.get(t)?.status === 'done';
	const hasMath = $derived(!!game?.hasMath || (math !== null && math.tier !== 'none') || doneTool('math_preview') || doneTool('math_candidate'));
	const frozenNow = $derived(locked || !!math?.frozenLookups);
	// end time of the newest successful math run (ISO strings compare in time order)
	const lastMathEnd = $derived(
		MATH_TOOLS.map((t) => lastByTool.get(t))
			.filter((j): j is Job => j?.status === 'done' && !!j.ended)
			.map((j) => j.ended as string)
			.sort()
			.pop() ?? null,
	);

	/** Status of a step: from the last job of its last tool (or any running tool of the step). */
	function stepStatus(s: Step): { key: string; text: string; when: string | null } {
		const lastJobs = s.tools.map((t) => lastByTool.get(t));
		const run = lastJobs.find((j) => j?.status === 'running');
		if (run) return { key: 'running', text: 'Running', when: run.started };
		if (s.n === 7 && frozenNow) return { key: 'done', text: locked ? 'Frozen (approved)' : 'Frozen', when: null };
		if (s.mathOnly && locked) return { key: 'skip', text: 'Not needed (math approved)', when: null };
		// combo: failed if any part failed after the start of the last run; done only if every part is done
		const last = lastJobs[lastJobs.length - 1];
		if (!last) return { key: 'none', text: 'Not run yet', when: null };
		const failed = lastJobs.find((j) => j && j.status !== 'done');
		if (failed) return { key: failed.status, text: STATUS_TEXT[failed.status] ?? failed.status, when: failed.started };
		if (s.n === 3 && lastMathEnd && lastMathEnd > last.started) return { key: 'old', text: 'Out of date (new math): run again', when: last.started };
		return { key: 'done', text: 'Finished', when: last.ended ?? last.started };
	}
	const stepDone = (n: number) => stepStatus(byN(n)).key === 'done' || stepStatus(byN(n)).key === 'skip';

	/** Why a step cannot run yet (one plain line), or null when it can. */
	function blocker(s: Step): string | null {
		if (s.mathOnly && locked) return 'This game’s math is approved and locked; it is not re-run here.';
		switch (s.n) {
			case 1:
				return null;
			case 2:
				return stepDone(1) ? null : 'Run step 1 (Prepare) first.';
			case 3:
				return hasMath ? null : 'Needs math results: run step 2 (Math estimate) first.';
			case 4:
				return stepDone(3) ? null : 'Needs current game data and preview data: run step 3 first.';
			case 5:
				return doneTool('web_build') ? null : 'Needs the built game: run step 4 first.';
			case 6:
				return stepDone(5) ? null : 'Run the quick check (step 5) first, so a 40-minute run is not wasted on a broken game.';
			case 7:
				if (frozenNow) return 'The math is already frozen.';
				if (math && math.tier === 'preview') return 'The last math run was only an estimate: run step 6 (Final math) first.';
				return doneTool('math_candidate') || math?.tier === 'candidate' ? null : 'Needs the final math: run step 6 first.';
			case 8:
				return frozenNow ? null : 'Freeze the math first (step 7): the full check tests the math you will ship.';
			case 9:
				return stepDone(8) ? null : 'Needs a passed full check (step 8).';
			case 10:
				return stepDone(9) ? null : 'Make the documents first (step 9).';
		}
		return null;
	}

	async function loadGame() {
		try {
			const all = await api<GameSummary[]>('/api/games');
			game = all.find((g) => g.id === id) ?? null;
		} catch {
			game = null;
		}
	}

	async function loadJobs() {
		jobsError = '';
		try {
			jobs = await api<Job[]>(`/api/game/${encodeURIComponent(id)}/jobs`);
		} catch (e) {
			jobsError = (e as Error).message;
			jobs = jobs ?? [];
		}
	}

	async function loadMath() {
		try {
			math = await api<MathState>(`/api/game/${encodeURIComponent(id)}/math-state`);
		} catch {
			math = null; // endpoint not there yet or failed: the page works without it
		}
	}

	const reload = () => Promise.all([loadGame(), loadJobs(), loadMath()]);

	/** Poll one job until it stops; streams its log into liveLog. */
	async function follow(j: Job): Promise<Job> {
		current = j;
		liveLog = '';
		let next = 0;
		for (;;) {
			if (destroyed) return j;
			try {
				const r = await api<{ job: Job; log: string; next: number }>(`/api/jobs/${encodeURIComponent(j.id)}?from=${next}`);
				if (r.log) liveLog += r.log;
				next = r.next;
				current = r.job;
				if (r.job.status !== 'running') return r.job;
			} catch (e) {
				runError = (e as Error).message;
			}
			await new Promise((res) => setTimeout(res, 800));
		}
	}

	/** Run one tool to the end. Returns true on success. */
	async function runTool(tool: ToolId): Promise<boolean> {
		let j: Job;
		try {
			j = await api<Job>(`/api/game/${encodeURIComponent(id)}/jobs`, sendJson('POST', { tool }));
		} catch (e) {
			runError = (e as Error).message;
			return false;
		}
		await loadJobs();
		const end = await follow(j);
		if (end.status === 'done' && MATH_TOOLS.includes(tool)) {
			// tell the math-state endpoint that the math now matches game.json
			try {
				const res = await fetch(`/api/game/${encodeURIComponent(id)}/math-state`, sendJson('POST', { stamp: true }));
				if (!res.ok && res.status !== 404) runError = `Math finished, but its date could not be saved: ${await errorText(res)}`;
			} catch {
				/* the server is gone; the next load shows it */
			}
		}
		await reload();
		return end.status === 'done';
	}

	/** Run a list of steps one after the other; stop at the first failure or cancel. */
	async function runSteps(label: string, steps: Step[]) {
		if (chain) return;
		for (const s of steps) if (s.confirm && !(s.mathOnly && locked) && !window.confirm(s.confirm)) return;
		const tools = steps.filter((s) => !(s.mathOnly && locked)).flatMap((s) => s.tools);
		runError = '';
		cancelled = false;
		chain = { label, tools, at: 0 };
		for (let i = 0; i < tools.length; i++) {
			if (cancelled || destroyed) break;
			chain = { label, tools, at: i };
			const ok = await runTool(tools[i]);
			if (!ok) {
				if (!cancelled && !runError) runError = `Stopped: “${TOOL_INFO[tools[i]]?.label ?? tools[i]}” did not finish. Read the red box and the log, fix the cause, then run again.`;
				break;
			}
		}
		chain = null;
	}

	async function cancel() {
		cancelled = true;
		if (!current || current.status !== 'running') return;
		try {
			current = await api<Job>(`/api/jobs/${encodeURIComponent(current.id)}/cancel`, { method: 'POST' });
		} catch (e) {
			runError = (e as Error).message;
		}
		await loadJobs();
	}

	async function view(j: Job) {
		viewing = { job: j, log: '', error: '' };
		try {
			const r = await api<{ job: Job; log: string; next: number }>(`/api/jobs/${encodeURIComponent(j.id)}?from=0`);
			if (viewing?.job.id === j.id) viewing = { job: r.job, log: r.log, error: '' };
		} catch (e) {
			if (viewing?.job.id === j.id) viewing = { ...viewing, error: (e as Error).message };
		}
	}

	const when = (iso: string) => new Date(iso).toLocaleString();
	const took = (j: Job) => (j.ended ? fmtDuration(Date.parse(j.ended) - Date.parse(j.started)) : '…');
	const stepMinutes = (s: Step) => s.tools.reduce((a, t) => a + (TOOL_INFO[t]?.minutes ?? 0), 0);

	// a job started earlier (other tab, before reload) is followed so its log shows here
	let attachedFor = '';
	$effect(() => {
		const running = (jobs ?? []).find((j) => j.status === 'running' && j.tool !== 'preview_server');
		if (running && !chain && current?.id !== running.id && attachedFor !== running.id) {
			attachedFor = running.id;
			follow(running).then(() => reload());
		}
	});

	$effect(() => {
		void id;
		game = null;
		jobs = null;
		math = null;
		viewing = null;
		current = null;
		liveLog = '';
		runError = '';
		reload();
	});

	onDestroy(() => {
		destroyed = true;
		clearInterval(ticker);
	});

	const busy = $derived(!!chain || current?.status === 'running');
	const firstFive = $derived(STEPS.slice(0, 5));
	const firstFiveBlocked = $derived(busy);
</script>

<svelte:head><title>{id} · Build & package</title></svelte:head>

<h1>Build & package</h1>
<p class="muted">
	Go through the steps in order. A grey step is waiting for an earlier one; the line under it says which. If a step fails, read the red
	box, fix the cause, and run that step again.
</p>

{#if math?.stale}
	<div class="panel stale" role="alert">
		<strong>Math is out of date:</strong> the game’s math settings changed after the last math run. Run step 2 (and 6) again.
	</div>
{/if}

<div class="panel chainbar">
	<button onclick={() => runSteps('Steps 1–5', firstFive)} disabled={firstFiveBlocked}>Run steps 1–5</button>
	<span class="muted">Runs Prepare → Math estimate → Prepare again + preview data → Build web → Quick check, one after the other, and stops at the first problem.</span>
</div>

<ol class="steps">
	{#each STEPS as s (s.n)}
		{@const st = stepStatus(s)}
		{@const why = blocker(s)}
		<li class="panel step" class:grey={!!why && st.key !== 'running'}>
			<div class="head">
				<span class="num">{s.n}</span>
				<div class="body">
					<h2>{s.title} <span class="st {st.key}">{st.text}</span></h2>
					<p class="muted">{s.what}</p>
					{#if s.warn && !(s.mathOnly && locked)}<p class="warn small">{s.warn}</p>{/if}
					{#if st.when}<p class="small muted">Last: {when(st.when)}</p>{/if}
					{#if why}<p class="small why">{why}</p>{/if}
				</div>
				<div class="act">
					<button onclick={() => runSteps(`Step ${s.n}`, [s])} disabled={busy || !!why}>{s.button}</button>
					<span class="small muted">about {fmtMinutes(stepMinutes(s))}</span>
				</div>
			</div>
		</li>
	{/each}
</ol>

{#if current || runError}
	<div class="panel live" aria-live="polite">
		<div class="vhead">
			<strong>
				{#if chain}{chain.label}: part {chain.at + 1} of {chain.tools.length} —{/if}
				{current ? (TOOL_INFO[current.tool]?.label ?? current.tool) : ''}
				{#if current}<span class="st {current.status}">{STATUS_TEXT[current.status] ?? current.status}</span>
					<span class="muted">{fmtDuration((current.ended ? Date.parse(current.ended) : now) - Date.parse(current.started))}</span>{/if}
			</strong>
			{#if busy}<button class="secondary" onclick={cancel}>Cancel</button>{/if}
		</div>
		{#if current?.status === 'failed'}
			<div class="errbox"><strong>It did not work.</strong> {current.plain ?? 'The step stopped with an error. The details are in the log below.'}</div>
		{/if}
		{#if runError}<div class="errbox" role="alert">{runError}</div>{/if}
		{#if current}<pre class="log" aria-label="Live log">{liveLog || (current.status === 'running' ? 'Waiting for output…' : '(no output)')}</pre>{/if}
	</div>
{/if}

<h2>Recent runs</h2>
<div class="panel">
	{#if jobsError}
		<p class="muted">Could not load the list of runs. {jobsError}</p>
	{:else if jobs === null}
		<p class="muted">Loading…</p>
	{:else if jobs.length === 0}
		<p class="muted">Nothing has been run for this game yet.</p>
	{:else}
		<table>
			<thead><tr><th>Step</th><th>Started</th><th>Took</th><th>Result</th><th></th></tr></thead>
			<tbody>
				{#each jobs.slice(0, 25) as j (j.id)}
					<tr>
						<td>{TOOL_INFO[j.tool]?.label ?? j.tool}</td>
						<td>{when(j.started)}</td>
						<td>{took(j)}</td>
						<td><span class="st {j.status}">{STATUS_TEXT[j.status] ?? j.status}</span></td>
						<td><button class="secondary" onclick={() => view(j)}>View log</button></td>
					</tr>
				{/each}
			</tbody>
		</table>
		<button class="secondary refresh" onclick={reload}>Refresh</button>
	{/if}
</div>

{#if viewing}
	<div class="panel viewer">
		<div class="vhead">
			<strong>{TOOL_INFO[viewing.job.tool]?.label ?? viewing.job.tool} — {when(viewing.job.started)}</strong>
			<button class="secondary" onclick={() => (viewing = null)}>Close</button>
		</div>
		{#if viewing.job.status === 'failed' && viewing.job.plain}
			<div class="errbox">{viewing.job.plain}</div>
		{/if}
		{#if viewing.error}
			<p class="muted">Could not load the log. {viewing.error}</p>
		{:else}
			<pre class="log" aria-label="Run log">{viewing.log || '(no output)'}</pre>
		{/if}
	</div>
{/if}

<style>
	.stale { border-color: var(--warn); color: var(--warn); margin-bottom: 10px; }
	.chainbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
	.steps { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
	.step.grey { opacity: 0.55; }
	.head { display: flex; gap: 12px; align-items: flex-start; }
	.body { flex: 1; }
	.head h2 { margin: 0; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
	.head p { margin: 2px 0 0; }
	.act { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex: none; }
	.num { flex: none; width: 28px; height: 28px; border-radius: 50%; background: var(--accent); color: #1b1446; font-weight: 800; display: grid; place-items: center; }
	.small { font-size: 12px; margin: 0; }
	.why { color: var(--warn); }
	.st { font-weight: 700; font-size: 12px; padding: 1px 8px; border-radius: 10px; border: 1px solid var(--line); background: #0f0d18; }
	.st.done { color: var(--ok); }
	.st.failed { color: var(--bad); }
	.st.running { color: var(--accent); }
	.st.cancelled, .st.none, .st.skip { color: var(--muted); }
	.st.old { color: var(--warn); }
	.live { margin-top: 12px; }
	table { width: 100%; border-collapse: collapse; }
	th, td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--line); }
	th { color: var(--muted); font-weight: 600; }
	.refresh { margin-top: 8px; }
	.viewer { margin-top: 12px; }
	.vhead { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px; }
	.errbox { background: #3a1714; border: 1px solid var(--bad); color: #ffd9d4; border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; white-space: pre-wrap; }
</style>
