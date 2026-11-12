<script lang="ts">
	// Submit page: everything the owner copies into the Stake Studio submission form (tools/release/pack.py).
	import { page } from '$app/state';
	import type { PackSummary } from '$lib/types';
	import JobPanel, { api } from '$lib/components/JobPanel.svelte';
	import Checklist from '$lib/components/Checklist.svelte';

	const id = $derived(page.params.id as string);

	let pack = $state<PackSummary | null>(null);
	let packError = $state('');
	let loading = $state(true);
	let version = $state('');
	let copied = $state('');

	const versionOk = $derived(version === '' || /^\d{1,6}$/.test(version));
	const fileUrl = (name: string) => `/api/game/${encodeURIComponent(id)}/pack/file?name=${encodeURIComponent(name)}`;
	const shots = $derived(pack?.files.filter((f) => f.path.startsWith('shots/')) ?? []);
	const docs = $derived(pack?.files.filter((f) => !f.path.startsWith('shots/')) ?? []);

	async function load() {
		loading = true;
		packError = '';
		try {
			pack = await api<PackSummary>(`/api/game/${encodeURIComponent(id)}/pack`);
		} catch (e) {
			pack = null;
			packError = (e as Error).message;
		} finally {
			loading = false;
		}
	}

	async function copy(label: string, value: string) {
		try {
			await navigator.clipboard.writeText(value);
			copied = label;
			setTimeout(() => copied === label && (copied = ''), 2000);
		} catch {
			copied = '';
			window.prompt('Copy this text (Ctrl+C):', value);
		}
	}

	$effect(() => {
		if (id) load();
	});
</script>

<h1>Submit to Stake</h1>
<p class="muted">
	This page makes the documents for the Stake Studio submission form. It never uploads or submits anything: you do that
	in Stake Studio. Guide: <code>docs\11-factory-guide.md</code>.
</p>

<section class="steps">
	<div class="panel">
		<h2>1. Reviewer event IDs</h2>
		<p class="muted small">
			Picks one round per mode for each outcome (loss, normal win, big win, bonus trigger, max win). Reviewers may ask for
			them. Enter the math version number Stake Studio shows after <em>Publish Game → Math</em>, so the replay links are
			complete. You can leave it empty for now and pick again later.
		</p>
		<label class="field">
			Studio math version
			<input bind:value={version} inputmode="numeric" placeholder="e.g. 3" size="8" aria-invalid={!versionOk} />
		</label>
		{#if !versionOk}<p class="bad small">The version is a number (e.g. 3).</p>{/if}
		<JobPanel game={id} tool="event_ids" label="Pick event IDs" opts={(version ? { version } : undefined) as any} disabled={!versionOk} disabledNote="Fix the version number first." />
	</div>

	<div class="panel">
		<h2>2. Screenshots</h2>
		<p class="muted small">
			Opens the game at the four reviewer sizes (1280×720, 1200×675, 400×225, 425×812) and saves a picture of each. Uses the
			game preview port 3007: stop a running preview first.
		</p>
		<JobPanel game={id} tool="shots" label="Take screenshots" />
	</div>

	<div class="panel">
		<h2>3. Submission pack</h2>
		<p class="muted small">
			Collects the form fields, math table, rules, event IDs, checklist, licences, screenshots and the upload list into one
			printable page. Run it again after any change.
		</p>
		<JobPanel game={id} tool="pack" label="Build submission pack" ondone={load} />
	</div>
</section>

<section class="checklist"><Checklist game={id} /></section>

<h2>Result</h2>
{#if loading}
	<p class="muted">Loading…</p>
{:else if !pack}
	<div class="panel muted">{packError || 'No submission pack yet.'} Press <strong>Build submission pack</strong> above.</div>
{:else}
	<div class="panel status {pack.ready ? 'ready' : 'notready'}">
		{#if pack.ready}
			<strong class="ok">Ready:</strong> no Stake-level problems. Warnings below are our own quality rules; you may still submit.
		{:else}
			<strong class="bad">Not ready:</strong> {pack.blockers.length} Stake-level problem(s) would make Stake reject the game. Fix the red items first.
		{/if}
		<span class="muted small">Pack of version {pack.version}, made {pack.generated ?? 'unknown'}.</span>
	</div>

	<div class="docs">
		{#each docs as f}
			<a class:primary={f.path === 'submission.html'} href={fileUrl(f.path)} target="_blank" rel="noopener">{f.label}</a>
		{/each}
	</div>

	{#if pack.blockers.length}
		<h2 class="bad">Blocks submission ({pack.blockers.length})</h2>
		<ul class="issues">
			{#each pack.blockers as b}
				<li class="blocker">
					<span>{b.message}</span>
					<span class="muted small">rule <code>{b.rule}</code>{#if b.source} · <a href={b.source.startsWith('http') ? b.source : undefined} target="_blank" rel="noopener">{b.source}</a>{/if}{#if b.why} · {b.why}{/if}</span>
				</li>
			{/each}
		</ul>
	{/if}

	{#if pack.warnings.length}
		<h2 class="warn">Warnings ({pack.warnings.length})</h2>
		<ul class="issues">
			{#each pack.warnings as w}
				<li class="warning">
					<span>{w.message}</span>
					{#if w.why}<span class="small"><strong>Why:</strong> {w.why}</span>{/if}
					<span class="muted small">rule <code>{w.rule}</code></span>
				</li>
			{/each}
		</ul>
	{/if}

	<h2>Studio form fields</h2>
	<p class="muted small">Copy each value into the matching field of the Stake Studio submission form.</p>
	<div class="fields">
		{#each pack.studioFields as f}
			<div class="panel field-row">
				<div class="flabel">{f.label}</div>
				<pre class="fvalue">{f.value}</pre>
				<button class="secondary" onclick={() => copy(f.label, f.value)}>{copied === f.label ? 'Copied' : 'Copy'}</button>
			</div>
		{/each}
	</div>

	{#if shots.length}
		<h2>Screenshots</h2>
		<div class="shots">
			{#each shots as s}
				<a href={fileUrl(s.path)} target="_blank" rel="noopener"><img src={fileUrl(s.path)} alt={s.label} /><span class="muted small">{s.label}</span></a>
			{/each}
		</div>
	{/if}
{/if}

<style>
	.steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
	.steps h2 { margin-top: 0; }
	.checklist { margin-top: 12px; }
	.small { font-size: 13px; }
	.field { display: flex; gap: 8px; align-items: center; margin: 6px 0 10px; }
	.status { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
	.status.ready { border-color: var(--ok); }
	.status.notready { border-color: var(--bad); }
	.docs { display: flex; gap: 10px; flex-wrap: wrap; margin: 8px 0; }
	.docs a { padding: 5px 10px; border: 1px solid var(--line); border-radius: 6px; text-decoration: none; }
	.docs a.primary { background: var(--accent); color: #1b1446; font-weight: 700; }
	.issues { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 6px; }
	.issues li { display: flex; flex-direction: column; gap: 2px; padding: 8px 10px; border-radius: 6px; }
	.blocker { background: #3a1714; border: 1px solid var(--bad); }
	.warning { background: #3a2f12; border: 1px solid var(--warn); }
	.fields { display: flex; flex-direction: column; gap: 8px; }
	.field-row { display: grid; grid-template-columns: 220px 1fr auto; gap: 10px; align-items: start; }
	.flabel { font-weight: 700; }
	.fvalue { margin: 0; white-space: pre-wrap; word-break: break-word; font: inherit; }
	.shots { display: flex; gap: 12px; flex-wrap: wrap; }
	.shots a { display: flex; flex-direction: column; gap: 4px; text-decoration: none; }
	.shots img { max-width: 320px; max-height: 240px; border: 1px solid var(--line); border-radius: 4px; }
</style>
