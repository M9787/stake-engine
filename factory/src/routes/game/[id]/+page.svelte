<script lang="ts">
	import { page } from '$app/state';
	import type { Definition, ValidateResult } from '$lib/types';
	import { api, sendJson } from '$lib/components/JobPanel.svelte';
	import Issues from '$lib/components/Issues.svelte';

	type Snapshot = { id: string; when: string; note: string };

	const id = $derived(page.params.id as string);

	let def = $state<Definition | null>(null);
	let saved = $state(''); // JSON of the last loaded/saved definition, for "unsaved changes"
	let loadError = $state('');
	let saving = $state(false);
	let saveError = $state('');
	let saveOk = $state('');
	let validation = $state<ValidateResult | null>(null);
	let search = $state('');

	let history = $state<Snapshot[] | null>(null);
	let historyError = $state('');
	let restoring = $state('');

	const frozen = $derived(!!def && (def.readOnly.modes || def.readOnly.math));
	const dirty = $derived(!!def && JSON.stringify(def) !== saved);

	// ---- theme helpers -----------------------------------------------------------------------
	const HEX = /^#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$/;
	const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
	const palette = $derived(def && isObj(def.theme.palette) ? (def.theme.palette as Record<string, unknown>) : null);
	const ui = $derived(def && isObj(def.theme.ui) ? (def.theme.ui as Record<string, unknown>) : null);
	const UI_LABELS: [string, string][] = [
		['text', 'Interface text'],
		['heading', 'Headings'],
		['rule', 'Divider lines'],
	];

	const pickerValue = (v: unknown) => {
		const m = typeof v === 'string' ? HEX.exec(v) : null;
		return m ? `#${m[1].toLowerCase()}` : '#000000';
	};
	function setColour(obj: Record<string, unknown>, key: string, picked: string) {
		const old = typeof obj[key] === 'string' ? (obj[key] as string) : '';
		const alpha = HEX.exec(old)?.[2] ?? '';
		obj[key] = picked.toUpperCase() + alpha.toUpperCase();
	}
	const colourOk = (v: unknown) => typeof v === 'string' && HEX.test(v);
	const nice = (k: string) => k.replace(/_/g, ' ');

	// ---- text helpers ------------------------------------------------------------------------
	const PH = /\{[^{}]+\}/g;
	type Part = { ph: boolean; s: string };
	const parts = (v: string): Part[] => {
		const out: Part[] = [];
		let last = 0;
		for (const m of v.matchAll(PH)) {
			if (m.index! > last) out.push({ ph: false, s: v.slice(last, m.index) });
			out.push({ ph: true, s: m[0].slice(1, -1) });
			last = m.index! + m[0].length;
		}
		if (last < v.length) out.push({ ph: false, s: v.slice(last) });
		return out;
	};
	const placeholders = (v: string) => [...v.matchAll(PH)].map((m) => m[0].slice(1, -1));
	const hasLooseDigits = (v: string) => /\d/.test(v.replace(PH, ''));

	const textKeys = $derived(def ? Object.keys(def.texts).filter((k) => !k.startsWith('_')) : []);
	const shownKeys = $derived.by(() => {
		const q = search.trim().toLowerCase();
		if (!def || !q) return textKeys;
		return textKeys.filter((k) => k.toLowerCase().includes(q) || def!.texts[k].toLowerCase().includes(q));
	});
	const digitWarnings = $derived(def ? textKeys.filter((k) => hasLooseDigits(def!.texts[k])).length : 0);

	// ---- load / save -------------------------------------------------------------------------
	async function load() {
		loadError = '';
		try {
			const d = await api<Definition>(`/api/game/${encodeURIComponent(id)}/definition`);
			def = d;
			saved = JSON.stringify(d);
		} catch (e) {
			loadError = (e as Error).message;
		}
	}

	async function loadHistory() {
		historyError = '';
		try {
			const raw = await api<unknown>(`/api/game/${encodeURIComponent(id)}/history`);
			const list = Array.isArray(raw) ? raw : isObj(raw) && Array.isArray(raw.snapshots) ? raw.snapshots : [];
			history = list.map((s: any) =>
				typeof s === 'string'
					? { id: s, when: s, note: '' }
					: { id: String(s.id ?? s.ts ?? s.name ?? ''), when: String(s.date ?? s.when ?? s.ts ?? s.id ?? ''), note: String(s.note ?? s.reason ?? '') },
			);
		} catch (e) {
			historyError = (e as Error).message;
			history = [];
		}
	}

	const isValidation = (v: any): v is ValidateResult => isObj(v) && Array.isArray(v.errors) && Array.isArray(v.warnings);

	async function save() {
		if (!def) return;
		saving = true;
		saveError = '';
		saveOk = '';
		try {
			const body = $state.snapshot(def);
			const r = await api<unknown>(`/api/game/${encodeURIComponent(id)}/definition`, sendJson('PUT', body));
			saved = JSON.stringify(def);
			saveOk = 'Saved.';
			const v: any = r;
			if (isValidation(v)) validation = v;
			else if (isObj(v) && isValidation(v.validation)) validation = v.validation as ValidateResult;
			else validation = await api<ValidateResult>(`/api/game/${encodeURIComponent(id)}/validate`).catch(() => null);
			loadHistory();
		} catch (e) {
			saveError = (e as Error).message;
		} finally {
			saving = false;
		}
	}

	async function restore(s: Snapshot) {
		if (!window.confirm(`Go back to the version saved ${fmtWhen(s.when)}? Your current version is kept in the history too.`)) return;
		restoring = s.id;
		saveError = '';
		saveOk = '';
		try {
			await api<unknown>(`/api/game/${encodeURIComponent(id)}/history`, sendJson('POST', { restore: s.id }));
			await load();
			await loadHistory();
			saveOk = 'Restored.';
			validation = await api<ValidateResult>(`/api/game/${encodeURIComponent(id)}/validate`).catch(() => null);
		} catch (e) {
			saveError = (e as Error).message;
		} finally {
			restoring = '';
		}
	}

	function fmtWhen(w: string) {
		// snapshot folders may be compact timestamps (20261107T101500) or ISO strings
		const m = /^(\d{4})(\d{2})(\d{2})[T_-]?(\d{2})(\d{2})(\d{2})?/.exec(w);
		const d = m ? new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6] ?? '00'}`) : new Date(w);
		return isNaN(d.getTime()) ? w : d.toLocaleString();
	}

	$effect(() => {
		// reload when the game id in the URL changes
		void id;
		def = null;
		validation = null;
		history = null;
		load();
		loadHistory();
	});
</script>

<svelte:head><title>{def?.identity.displayName ?? id} · Overview</title></svelte:head>

{#if loadError}
	<h1>{id}</h1>
	<div class="errbox" role="alert">Could not open this game. {loadError}</div>
	<p><a href="/">← Back to all games</a></p>
{:else if !def}
	<p class="muted">Loading…</p>
{:else}
	<div class="top">
		<h1>{def.identity.displayName}</h1>
		<div class="savebar">
			{#if dirty}<span class="warn">Unsaved changes</span>{:else if saveOk}<span class="ok">{saveOk}</span>{/if}
			<button onclick={save} disabled={saving || !dirty}>{saving ? 'Saving…' : 'Save'}</button>
		</div>
	</div>

	{#if frozen}
		<div class="notice" role="note">
			<strong>Approved game.</strong> Its bet modes and math are locked and cannot be changed here.
			You can still edit the name, colours and texts.
		</div>
	{/if}

	{#if saveError}<div class="errbox" role="alert">Could not save. {saveError}</div>{/if}
	{#if validation}
		<div class="panel"><Issues result={validation} okText="Saved and all checks pass." /></div>
	{/if}

	<div class="grid">
		<section class="panel">
			<h2>Name and version</h2>
			<label class="field"><span>Display name</span><input bind:value={def.identity.displayName} /></label>
			<label class="field">
				<span>Version</span>
				<input bind:value={def.identity.version} placeholder="1.0.0" aria-describedby="ver-help" />
			</label>
			<p id="ver-help" class="muted small">Three numbers like 1.0.0. Raise it before packaging a changed game.</p>
		</section>

		<section class="panel">
			<h2>Mode</h2>
			<fieldset class="modes" aria-describedby="mode-help">
				<legend class="sr">Factory mode</legend>
				<label class="mode" class:on={def.release.mode === 'test'}>
					<input type="radio" name="release-mode" value="test" bind:group={def.release.mode} />
					<span>
						<strong>Test</strong>
						<span class="muted small block">
							Any art and sound is allowed: unedited AI images, test placeholders, anything. No licence, source, human-edit or
							sign-off checks, and no licence list in the package. All Stake rules still apply (100,000 simulations, math tests,
							front-end rules, tile and cover images, wording). The package is a real Studio upload and can be submitted for review.
						</span>
					</span>
				</label>
				<label class="mode" class:on={def.release.mode === 'release'}>
					<input type="radio" name="release-mode" value="release" bind:group={def.release.mode} />
					<span>
						<strong>Release</strong>
						<span class="muted small block">
							All rules: every art slot filled, no test assets, each image edited by a person, licence and source for every file,
							art signed off. Packaging refuses while test assets are in the game.
						</span>
					</span>
				</label>
			</fieldset>
			<p id="mode-help" class="muted small">Press Save to apply. Run the full check again after switching: packaging needs a check run in this mode.</p>
		</section>

		<section class="panel">
			<h2>Colours</h2>
			{#if palette}
				<h3>Palette</h3>
				<div class="colours">
					{#each Object.keys(palette) as k (k)}
						<label class="colour">
							<input type="color" value={pickerValue(palette[k])} oninput={(e) => setColour(palette, k, e.currentTarget.value)} aria-label={`Palette colour ${nice(k)}`} />
							<span>{nice(k)}</span>
							<code class:bad={!colourOk(palette[k])}>{palette[k]}</code>
						</label>
					{/each}
				</div>
			{/if}
			{#if ui}
				<h3>Interface</h3>
				<div class="colours">
					{#each UI_LABELS as [k, l] (k)}
						{#if k in ui}
							<label class="colour">
								<input type="color" value={pickerValue(ui[k])} oninput={(e) => setColour(ui, k, e.currentTarget.value)} aria-label={l} />
								<span>{l}</span>
								<code class:bad={!colourOk(ui[k])}>{ui[k]}</code>
							</label>
						{/if}
					{/each}
				</div>
				<p class="muted small">Transparency (if any) is kept when you pick a new colour.</p>
			{/if}
			{#if !palette && !ui}<p class="muted">This game has no editable colours.</p>{/if}
		</section>
	</div>

	<section class="panel texts">
		<div class="texthead">
			<h2>Texts</h2>
			<input type="search" bind:value={search} placeholder="Search texts…" aria-label="Search texts" />
		</div>
		<p class="muted small">
			Words in <span class="chip">boxes</span> are filled in automatically (numbers from the math). Keep them as they are and do not type
			numbers yourself.
			{#if digitWarnings}<span class="warn">{digitWarnings} text{digitWarnings === 1 ? '' : 's'} contain typed numbers.</span>{/if}
		</p>
		<table>
			<thead><tr><th>Where it is used</th><th>Text</th></tr></thead>
			<tbody>
				{#each shownKeys as k (k)}
					{@const v = def.texts[k]}
					<tr>
						<td class="key"><code>{k}</code></td>
						<td>
							<textarea rows={v.length > 70 ? 3 : 1} bind:value={def.texts[k]} aria-label={`Text ${k}`}></textarea>
							{#if placeholders(v).length}
								<div class="chips">
									{#each parts(v) as p}{#if p.ph}<span class="chip">{p.s}</span>{/if}{/each}
								</div>
							{/if}
							{#if hasLooseDigits(v)}
								<p class="warn small">This text contains a typed number. Numbers must come from a placeholder in braces so they always match the math.</p>
							{/if}
						</td>
					</tr>
				{:else}
					<tr><td colspan="2" class="muted">No text matches “{search}”.</td></tr>
				{/each}
			</tbody>
		</table>
	</section>

	<section class="panel">
		<h2>History</h2>
		<p class="muted small">A copy is kept every time you save. You can go back to any of them.</p>
		{#if historyError}
			<p class="muted">History is not available: {historyError}</p>
		{:else if history === null}
			<p class="muted">Loading…</p>
		{:else if history.length === 0}
			<p class="muted">No saved versions yet.</p>
		{:else}
			<ul class="history">
				{#each history as s (s.id)}
					<li>
						<span>{fmtWhen(s.when)}</span>
						{#if s.note}<span class="muted">{s.note}</span>{/if}
						<button class="secondary" onclick={() => restore(s)} disabled={!!restoring}>{restoring === s.id ? 'Restoring…' : 'Restore'}</button>
					</li>
				{/each}
			</ul>
		{/if}
	</section>
{/if}

<style>
	.top { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
	.savebar { display: flex; gap: 10px; align-items: center; position: sticky; top: 50px; }
	.notice { background: #2e2814; border: 1px solid var(--accent); border-radius: 6px; padding: 8px 10px; margin-bottom: 12px; }
	.errbox { background: #3a1714; border: 1px solid var(--bad); color: #ffd9d4; border-radius: 6px; padding: 8px 10px; margin: 8px 0; }
	.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 12px; margin: 12px 0; }
	section h2 { margin-top: 0; }
	h3 { font-size: 13px; color: var(--muted); margin: 10px 0 6px; font-weight: 600; }
	.field { display: grid; grid-template-columns: 110px 1fr; align-items: center; gap: 8px; margin-bottom: 8px; }
	.small { font-size: 12px; margin: 4px 0; }
	.colours { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 8px; }
	.colour { display: grid; grid-template-columns: 38px 1fr; grid-template-rows: auto auto; column-gap: 8px; align-items: center; }
	.colour input[type='color'] { grid-row: span 2; width: 38px; height: 38px; padding: 2px; cursor: pointer; }
	.colour code { font-size: 11px; color: var(--muted); }
	code.bad { color: var(--bad); }
	.texts { margin: 12px 0; }
	.texthead { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
	.texthead input { width: 280px; }
	table { width: 100%; border-collapse: collapse; margin-top: 8px; }
	th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
	th { color: var(--muted); font-weight: 600; }
	td.key { width: 28%; word-break: break-all; }
	td.key code { font-size: 12px; color: var(--muted); }
	textarea { width: 100%; resize: vertical; }
	.chips { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px; }
	.chip { display: inline-block; font-size: 11px; padding: 0 6px; border-radius: 4px; background: #2a2450; border: 1px solid #4b4390; color: #cfc6ff; }
	.modes { border: 0; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
	.mode { display: grid; grid-template-columns: 22px 1fr; gap: 6px; align-items: start; padding: 8px; border: 1px solid var(--line); border-radius: 6px; cursor: pointer; }
	.mode.on { border-color: var(--accent); }
	.mode input { margin-top: 3px; }
	.block { display: block; }
	.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
	.history { list-style: none; padding: 0; margin: 0; }
	.history li { display: flex; gap: 12px; align-items: center; padding: 5px 0; border-bottom: 1px solid var(--line); }
	.history li button { margin-left: auto; }
</style>
