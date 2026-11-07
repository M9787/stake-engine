<script lang="ts">
	import { page } from '$app/state';
	import type { Job } from '$lib/types';
	import JobPanel, { api, sendJson } from '$lib/components/JobPanel.svelte';

	const id = $derived(page.params.id as string);
	const GAME_URL = 'https://localhost:3007/?sessionID=demo&rgs_url=localhost:3007/rgs&lang=en';
	const SIZES = [
		{ w: 1280, h: 720, label: 'Desktop 1280 × 720' },
		{ w: 400, h: 225, label: 'Small popout 400 × 225' },
		{ w: 425, h: 812, label: 'Mobile 425 × 812' },
	];

	let attach = $state<string | undefined>(undefined);
	let job = $state<Job | null>(null);
	let size = $state(SIZES[0]);
	let frameKey = $state(0);
	let checked = $state(false);

	type Ready = { skin: boolean; mock: boolean; running: { game: string; jobId: string } | null };
	let ready = $state<Ready | null>(null);
	let readyError = $state('');
	let preparing = $state<string | null>(null); // label of the part running now
	let prepError = $state('');
	let stopping = $state(false);

	const running = $derived(job?.status === 'running');
	const other = $derived(ready?.running && ready.running.game !== id ? ready.running : null);
	const dataOk = $derived(!!ready && ready.skin && ready.mock);

	async function findRunning() {
		readyError = '';
		try {
			ready = await api<Ready>(`/api/game/${encodeURIComponent(id)}/preview-ready`);
			attach = ready.running && ready.running.game === id ? ready.running.jobId : undefined;
		} catch (e) {
			ready = null;
			readyError = (e as Error).message;
			attach = undefined;
		} finally {
			checked = true;
		}
	}

	/** Wait for a job to stop; true when it finished without error. */
	async function waitJob(j: Job): Promise<Job> {
		for (;;) {
			const r = await api<{ job: Job }>(`/api/jobs/${encodeURIComponent(j.id)}?from=0`);
			if (r.job.status !== 'running') return r.job;
			await new Promise((res) => setTimeout(res, 1000));
		}
	}

	/** Prepare (sync: rules + skin data) then preview data (mock), stopping at the first failure. */
	async function prepare() {
		prepError = '';
		for (const [tool, label] of [['sync', 'Preparing the game data'], ['mock', 'Making the preview data']] as const) {
			preparing = label;
			try {
				const j = await api<Job>(`/api/game/${encodeURIComponent(id)}/jobs`, sendJson('POST', { tool }));
				const end = await waitJob(j);
				if (end.status !== 'done') {
					prepError = `${label} did not work. ${end.plain ?? ''} The full log is on the Build page (Recent runs).`;
					break;
				}
			} catch (e) {
				prepError = (e as Error).message;
				break;
			}
		}
		preparing = null;
		await findRunning();
	}

	async function stopOther() {
		if (!other) return;
		stopping = true;
		try {
			await api<Job>(`/api/jobs/${encodeURIComponent(other.jobId)}/cancel`, { method: 'POST' });
		} catch (e) {
			readyError = (e as Error).message;
		}
		stopping = false;
		await findRunning();
	}

	$effect(() => {
		void id;
		job = null;
		attach = undefined;
		checked = false;
		ready = null;
		prepError = '';
		findRunning();
	});
</script>

<svelte:head><title>{id} · Preview</title></svelte:head>

<h1>Preview</h1>

<div class="panel intro">
	<p>
		The preview shows the game as a player will see it. It needs the <strong>game server</strong> running on this computer.
		Press <em>Start preview</em> and wait until the status says <em>Running</em> (about half a minute the first time).
	</p>
	<ul class="muted">
		<li>The preview shows the game that was open when the server was started. Only one game can be previewed at a time: to see another game, press Cancel here, open that game and start the preview from there.</li>
		<li>After you change texts, colours or art, run <a href={`/game/${id}/build`}>Sync</a> (step 1), then press <em>Reload</em> below.</li>
	</ul>
</div>

{#if checked && readyError}
	<div class="panel bad">Could not check whether the preview can start. {readyError} <button class="secondary" onclick={findRunning}>Try again</button></div>
{/if}
{#if checked && ready && !dataOk && !running}
	<div class="panel need">
		<p>
			<strong>The preview needs data that is not there yet:</strong>
			{[!ready.skin && 'the game’s screen data (rules and skin)', !ready.mock && 'sample spins (preview data)'].filter(Boolean).join(' and ')}.
			Both are made from the math, so the game needs a math run first (Build page, step 2).
		</p>
		<button onclick={prepare} disabled={!!preparing}>{preparing ? `${preparing}…` : 'Make the missing data'}</button>
		{#if prepError}<div class="errbox" role="alert">{prepError}</div>{/if}
	</div>
{/if}
{#if checked && other}
	<div class="panel need">
		<p>
			A preview of another game (<strong>{other.game}</strong>) is running. Only one preview can run at a time, because they all use the same
			address on this computer. Stop it to preview this game.
		</p>
		<button onclick={stopOther} disabled={stopping}>{stopping ? 'Stopping…' : `Stop the ${other.game} preview`}</button>
	</div>
{/if}
{#if checked}
	<JobPanel
		game={id}
		tool="preview_server"
		label="Start preview"
		{attach}
		disabled={!running && (!dataOk || !!other || !!preparing)}
		disabledNote={other ? 'Stop the other preview first.' : 'Make the missing data first (above).'}
		onchange={(j) => (job = j)}
		ondone={(j) => {
			job = j;
			findRunning();
		}}
	/>
{:else}
	<p class="muted">Checking whether the preview is already running…</p>
{/if}

{#if running}
	<div class="panel cert">
		<p>
			<strong>First time?</strong> The preview uses a home-made security certificate, so your browser may show a blank frame below.
			<a href={GAME_URL} target="_blank" rel="noopener noreferrer">Open the game in a new tab</a>, choose “Advanced” → “Continue to localhost”,
			then come back and press Reload.
		</p>
	</div>

	<div class="toolbar" role="group" aria-label="Preview size">
		{#each SIZES as s}
			<button class:secondary={size !== s} onclick={() => (size = s)} aria-pressed={size === s}>{s.label}</button>
		{/each}
		<button class="secondary" onclick={() => frameKey++}>Reload</button>
	</div>

	<div class="stage">
		{#key frameKey}
			<iframe title="Game preview" src={GAME_URL} width={size.w} height={size.h} allow="autoplay; fullscreen"></iframe>
		{/key}
	</div>
{:else if checked && job && job.status !== 'running'}
	<p class="muted">The preview is stopped. Press <em>Start preview</em> to start it again.</p>
{/if}

<style>
	.intro p { margin: 0 0 6px; }
	.intro ul { margin: 0; padding-left: 18px; }
	.cert { margin: 12px 0; border-color: var(--warn); }
	.cert p { margin: 0; }
	.need { margin: 12px 0; border-color: var(--warn); display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
	.need p { margin: 0; }
	.bad { margin: 12px 0; border-color: var(--bad); }
	.errbox { background: #3a1714; border: 1px solid var(--bad); color: #ffd9d4; border-radius: 6px; padding: 8px 10px; white-space: pre-wrap; }
	.toolbar { display: flex; gap: 6px; flex-wrap: wrap; margin: 10px 0; }
	.stage { overflow: auto; background: #000; border: 1px solid var(--line); border-radius: 6px; padding: 10px; display: flex; justify-content: center; }
	iframe { border: 0; background: #000; flex: none; }
</style>
