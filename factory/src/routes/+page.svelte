<script lang="ts">
	import { onMount } from 'svelte';
	import type { DoctorRow, GameSummary, StudioSettings, ValidateResult } from '$lib/types';
	import { api, sendJson } from '$lib/components/JobPanel.svelte';
	import Issues from '$lib/components/Issues.svelte';

	let games = $state<GameSummary[] | null>(null);
	let gamesError = $state('');
	let doctor = $state<DoctorRow[] | null>(null);
	let doctorError = $state('');
	let doctorLoading = $state(false);

	// new game form
	let template = $state('');
	let newId = $state('');
	let newName = $state('');
	let creating = $state(false);
	let createError = $state('');
	let created = $state<{ id: string; validation: ValidateResult | null; validationError: string } | null>(null);

	// studio settings (factory/settings.json): provider fields for new games
	let settings = $state<StudioSettings | null>(null);
	let settingsSaved = $state('');
	let settingsError = $state('');
	let settingsOk = $state('');
	let settingsSaving = $state(false);
	const PROVIDER_RE = /^[a-z0-9_]{1,40}$/;
	const settingsDirty = $derived(!!settings && JSON.stringify(settings) !== settingsSaved);
	const providerProblem = $derived(
		settings && settings.providerName && !PROVIDER_RE.test(settings.providerName) ? 'Small letters, digits and _ only (at most 40).' : '',
	);

	async function loadSettings() {
		settingsError = '';
		try {
			settings = await api<StudioSettings>('/api/settings');
			settingsSaved = JSON.stringify(settings);
		} catch (e) {
			settingsError = (e as Error).message;
		}
	}

	async function saveSettings(ev: SubmitEvent) {
		ev.preventDefault();
		if (!settings) return;
		settingsSaving = true;
		settingsError = '';
		settingsOk = '';
		try {
			const body = { ...$state.snapshot(settings), providerNumber: Number(settings.providerNumber) };
			settings = await api<StudioSettings>('/api/settings', sendJson('PUT', body));
			settingsSaved = JSON.stringify(settings);
			settingsOk = 'Saved. New games use these values.';
		} catch (e) {
			settingsError = (e as Error).message;
		} finally {
			settingsSaving = false;
		}
	}

	const ID_RE = /^[a-z][a-z0-9_]{2,31}$/;
	const templates = $derived(
		games ? [...new Map(games.map((g) => [g.skin, g])).values()].map((g) => ({ skin: g.skin, name: g.displayName })) : [],
	);
	const idProblem = $derived(
		!newId
			? ''
			: !ID_RE.test(newId)
				? 'Use 3 to 32 characters: small letters, digits and _ only, starting with a letter.'
				: games?.some((g) => g.id === newId)
					? 'A game with this id already exists.'
					: '',
	);
	const canCreate = $derived(!!template && !!newId && !idProblem && newName.trim().length > 0 && !creating);

	async function loadGames() {
		gamesError = '';
		try {
			games = await api<GameSummary[]>('/api/games');
			if (!template && games.length) template = games.find((g) => !g.frozenModes)?.skin ?? games[0].skin;
		} catch (e) {
			gamesError = (e as Error).message;
			games = [];
		}
	}

	async function loadDoctor() {
		doctorLoading = true;
		doctorError = '';
		try {
			doctor = await api<DoctorRow[]>('/api/doctor');
		} catch (e) {
			doctorError = (e as Error).message;
		} finally {
			doctorLoading = false;
		}
	}

	async function createGame(ev: SubmitEvent) {
		ev.preventDefault();
		if (!canCreate) return;
		creating = true;
		createError = '';
		created = null;
		try {
			const r = await api<{ id: string }>('/api/games', sendJson('POST', { template, id: newId, displayName: newName.trim() }));
			let validation: ValidateResult | null = null;
			let validationError = '';
			try {
				validation = await api<ValidateResult>(`/api/game/${encodeURIComponent(r.id)}/validate`);
			} catch (e) {
				validationError = (e as Error).message;
			}
			created = { id: r.id, validation, validationError };
			newId = '';
			newName = '';
			await loadGames();
		} catch (e) {
			createError = (e as Error).message;
		} finally {
			creating = false;
		}
	}

	const pct = (g: GameSummary) => (g.requiredSlots.total ? Math.round((100 * g.requiredSlots.filled) / g.requiredSlots.total) : 0);

	onMount(() => {
		loadGames();
		loadDoctor();
		loadSettings();
	});
</script>

<svelte:head><title>Stake Game Factory</title></svelte:head>

<h1>Your games</h1>

{#if games === null}
	<p class="muted">Loading games…</p>
{:else}
	{#if gamesError}
		<div class="errbox" role="alert">Could not load the game list. {gamesError}</div>
	{/if}
	{#if games.length === 0 && !gamesError}
		<p class="muted">No games yet. Create one below.</p>
	{/if}
	<div class="cards">
		{#each games as g (g.id)}
			<a class="card panel" href={`/game/${g.id}`}>
				<div class="title">
					<strong>{g.displayName}</strong>
					<span class="muted id">{g.id}</span>
				</div>
				<div class="badges">
					{#if g.mode === 'test'}<span class="badge testmode" title="Test mode: any assets allowed, all Stake rules still apply">TEST</span>{/if}
					{#if g.testOnly}<span class="badge test">test only</span>{/if}
					{#if g.frozenModes}<span class="badge frozen" title="Bet modes and math are approved and locked">frozen</span>{/if}
					{#if !g.hasMath}<span class="badge nomath" title="The math has not been run yet">no math yet</span>{/if}
					<span class="badge">v{g.version}</span>
				</div>
				<div class="muted">Board: {g.board.reels} reels × {g.board.rows} rows</div>
				<div class="muted">
					Modes:
					{#each g.modes as m, i}{i ? ', ' : ''}{m.name}{m.kind === 'buy' ? ` (buy, ${m.cost}× bet)` : ''}{/each}
				</div>
				<div class="art">
					<span class="muted">Required art: {g.requiredSlots.filled} of {g.requiredSlots.total}</span>
					<div class="bar" role="progressbar" aria-label="Required art filled" aria-valuemin="0" aria-valuemax={g.requiredSlots.total} aria-valuenow={g.requiredSlots.filled}>
						<div class="fill" class:full={pct(g) === 100} style:width={`${pct(g)}%`}></div>
					</div>
				</div>
				<span class="open">Open →</span>
			</a>
		{/each}
	</div>
{/if}

<h2>New game</h2>
<form class="panel newgame" onsubmit={createGame}>
	<p class="muted">A new game starts as a copy of an existing one. You then change its name, colours, texts and art.</p>
	<label>
		<span>Start from</span>
		<select bind:value={template} disabled={!templates.length}>
			{#each templates as t}
				<option value={t.skin}>{t.name} ({t.skin})</option>
			{/each}
		</select>
	</label>
	<label>
		<span>Game id</span>
		<input bind:value={newId} placeholder="e.g. lucky_lanterns" autocomplete="off" spellcheck="false" aria-describedby="id-help" />
	</label>
	<p id="id-help" class:bad={!!idProblem} class:muted={!idProblem} class="help">
		{idProblem || 'Short internal name. Small letters, digits and _ only. It cannot be changed later.'}
	</p>
	<label>
		<span>Display name</span>
		<input bind:value={newName} placeholder="e.g. Lucky Lanterns" />
	</label>
	<div>
		<button type="submit" disabled={!canCreate}>{creating ? 'Creating…' : 'Create game'}</button>
	</div>
	{#if createError}
		<div class="errbox" role="alert">Could not create the game. {createError}</div>
	{/if}
	{#if created}
		<div class="created">
			<p class="ok"><strong>Game “{created.id}” created.</strong></p>
			{#if created.validation}
				<Issues result={created.validation} okText="The new game passes all checks." />
			{:else if created.validationError}
				<p class="muted">Could not run the checks yet: {created.validationError}</p>
			{/if}
			<p>Next step: <a href={`/game/${created.id}`}>open the game and give it its own name, colours and texts →</a></p>
		</div>
	{/if}
</form>

<h2>Studio settings</h2>
<form class="panel newgame" onsubmit={saveSettings}>
	<p class="muted">Your Stake Studio provider details. Entered once; every new game gets them. Existing games keep theirs.</p>
	{#if settingsError}<div class="errbox" role="alert">Could not load or save the settings. {settingsError}</div>{/if}
	{#if settings}
		<label>
			<span>Provider name</span>
			<input bind:value={settings.providerName} placeholder="e.g. lantern_studio" autocomplete="off" spellcheck="false" aria-describedby="prov-help" />
		</label>
		<p id="prov-help" class:bad={!!providerProblem} class:muted={!providerProblem} class="help">
			{providerProblem || 'As in your Studio team settings: small letters, digits and _.'}
		</p>
		<label>
			<span>Provider number</span>
			<input type="number" min="0" step="1" bind:value={settings.providerNumber} />
		</label>
		<label>
			<span>Team name</span>
			<input bind:value={settings.teamName} placeholder="e.g. Lantern Studio" />
		</label>
		<div class="savesettings">
			<button type="submit" disabled={settingsSaving || !settingsDirty || !!providerProblem || !settings.providerName}>{settingsSaving ? 'Saving…' : 'Save settings'}</button>
			{#if settingsOk && !settingsDirty}<span class="ok">{settingsOk}</span>{/if}
		</div>
	{:else if !settingsError}
		<p class="muted">Loading…</p>
	{/if}
</form>

<h2>Computer check</h2>
<div class="panel">
	<div class="doctorhead">
		<p class="muted">Checks that the tools the factory needs are installed in the right versions.</p>
		<button class="secondary" onclick={loadDoctor} disabled={doctorLoading}>{doctorLoading ? 'Checking…' : 'Check again'}</button>
	</div>
	{#if doctorError}
		<div class="errbox" role="alert">Could not run the check. {doctorError}</div>
	{:else if doctor === null}
		<p class="muted">Checking…</p>
	{:else}
		{@const fails = doctor.filter((r) => r.status === 'FAIL').length}
		<p class={fails ? 'bad' : 'ok'}>
			{fails ? `${fails} tool${fails === 1 ? '' : 's'} need fixing before building games.` : 'All required tools are ready.'}
		</p>
		<table>
			<thead><tr><th>Tool</th><th>Needed</th><th>Found</th><th>Status</th><th>How to fix</th></tr></thead>
			<tbody>
				{#each doctor as r}
					<tr>
						<td>{r.tool}</td>
						<td>{r.want}</td>
						<td>{r.have}</td>
						<td><span class="st {r.status}">{r.status === 'PASS' ? 'OK' : r.status === 'WARN' ? 'Check' : 'Missing'}</span></td>
						<td>{r.status === 'PASS' ? '' : r.fix}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>

<style>
	.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 12px; }
	.card { display: flex; flex-direction: column; gap: 6px; color: var(--text); text-decoration: none; }
	.card:hover, .card:focus-visible { border-color: var(--accent); }
	.title { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
	.title strong { font-size: 16px; }
	.id { font-family: ui-monospace, monospace; font-size: 12px; }
	.badges { display: flex; gap: 6px; flex-wrap: wrap; }
	.badge { font-size: 11px; padding: 1px 7px; border-radius: 9px; border: 1px solid var(--line); color: var(--muted); }
	.badge.test { color: #9fc3ff; border-color: #4a6aa0; }
	.badge.testmode { color: #0f0d18; background: #9fc3ff; border-color: #9fc3ff; font-weight: 700; }
	.savesettings { display: flex; gap: 10px; align-items: center; }
	.badge.frozen { color: var(--accent); border-color: var(--accent); }
	.badge.nomath { color: var(--warn); border-color: var(--warn); }
	.bar { height: 8px; background: #0f0d18; border: 1px solid var(--line); border-radius: 5px; overflow: hidden; margin-top: 3px; }
	.fill { height: 100%; background: var(--warn); }
	.fill.full { background: var(--ok); }
	.open { color: var(--accent); align-self: flex-end; font-weight: 700; }
	.newgame { display: flex; flex-direction: column; gap: 8px; max-width: 560px; }
	.newgame label { display: grid; grid-template-columns: 120px 1fr; align-items: center; gap: 8px; }
	.help { margin: -4px 0 0 128px; font-size: 12px; }
	.newgame p { margin: 0; }
	.created { border-top: 1px solid var(--line); padding-top: 8px; display: flex; flex-direction: column; gap: 6px; }
	.errbox { background: #3a1714; border: 1px solid var(--bad); color: #ffd9d4; border-radius: 6px; padding: 8px 10px; margin: 6px 0; }
	.doctorhead { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
	.doctorhead p { margin: 0; }
	table { width: 100%; border-collapse: collapse; margin-top: 8px; }
	th, td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
	th { color: var(--muted); font-weight: 600; }
	.st { font-weight: 700; padding: 1px 8px; border-radius: 9px; }
	.st.PASS { color: var(--ok); }
	.st.WARN { color: var(--warn); }
	.st.FAIL { color: #fff; background: var(--bad); }
</style>
