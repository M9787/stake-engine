<script lang="ts">
	// Features: grid multiplier (on/off, cap), bonus variants (scatter range, pre-charge, lowest bought win),
	// free spins per scatter count (base game) and extra spins on a retrigger (in the bonus).
	import { saveSection, copy, type SaveResult } from './save';
	import SaveBar from './SaveBar.svelte';

	let {
		game,
		features,
		freespinTriggers,
		cells,
		readOnly,
		onsaved,
	}: { game: string; features: any; freespinTriggers: any; cells: number; readOnly: boolean; onsaved: (r: SaveResult) => void } = $props();

	let form = $state({ features: copy(features), freespinTriggers: copy(freespinTriggers) });
	const start = JSON.stringify({ features, freespinTriggers });
	let busy = $state(false);
	let error = $state('');
	let ok = $state('');
	const dirty = $derived(JSON.stringify(form) !== start);
	const counts = $derived(Object.keys(form.freespinTriggers.basegame).map(Number).sort((a, b) => a - b));

	/** Set the same value for a count and every higher count (long tables). */
	function setFrom(kind: 'basegame' | 'freegame', from: number, value: number) {
		for (const k of Object.keys(form.freespinTriggers[kind])) if (Number(k) >= from) form.freespinTriggers[kind][k] = value;
	}

	async function save() {
		busy = true;
		error = '';
		ok = '';
		try {
			const r = await saveSection(game, 'features', form);
			ok = 'Saved.';
			onsaved(r);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			busy = false;
		}
	}
</script>

<div class="grid">
	<section class="panel">
		<h3>Grid multiplier</h3>
		<p class="muted small">Each winning spot charges up and doubles on every new win there (x2, x4, …) up to the cap.</p>
		<label class="f"><span>Turned on</span><input type="checkbox" bind:checked={form.features.gridMultiplier.enabled} disabled={readOnly} aria-label="Grid multiplier on" /></label>
		<label class="f"><span>Highest multiplier</span><input type="number" min="2" max="4096" bind:value={form.features.gridMultiplier.cap} disabled={readOnly} aria-label="Grid cap" /></label>
	</section>

	{#each form.features.bonusVariants as v (v.id)}
		<section class="panel">
			<h3>Bonus <code>{v.id}</code></h3>
			<p class="muted small">Starts when this many scatters land. Ranges of different bonuses must not overlap.</p>
			<label class="f"><span>Scatters from</span><input type="number" min="2" max={cells} bind:value={v.scatterMin} disabled={readOnly} aria-label={`${v.id} scatters from`} /></label>
			<label class="f"><span>Scatters up to</span><input type="number" min="2" max={cells} bind:value={v.scatterMax} disabled={readOnly} aria-label={`${v.id} scatters to`} /></label>
			<label class="f"><span>Spots charged at start</span><input type="number" min="0" max={cells} bind:value={v.precharge.spots} disabled={readOnly} aria-label={`${v.id} precharged spots`} /></label>
			<label class="f"><span>Their multiplier</span><input type="number" min="2" max="1024" bind:value={v.precharge.value} disabled={readOnly} aria-label={`${v.id} precharge value`} /></label>
			<label class="f"><span>Lowest win when started directly (x bet)</span><input type="number" min="0" bind:value={v.buyFloor} disabled={readOnly} aria-label={`${v.id} lowest bought win`} /></label>
		</section>
	{/each}
</div>

<details>
	<summary>Free spins per scatter count</summary>
	<p class="muted small">
		How many free spins the bonus gives for each number of scatters, and how many extra spins landing them again inside the bonus gives.
		Changing a value also sets every higher count.
	</p>
	<table>
		<thead><tr><th>Scatters</th><th>Free spins (start)</th><th>Extra spins (retrigger)</th></tr></thead>
		<tbody>
			{#each counts as c (c)}
				<tr>
					<td>{c}</td>
					<td><input type="number" min="0" value={form.freespinTriggers.basegame[String(c)]} disabled={readOnly} aria-label={`Free spins for ${c} scatters`}
						onchange={(e) => setFrom('basegame', c, Number(e.currentTarget.value))} /></td>
					<td><input type="number" min="0" value={form.freespinTriggers.freegame[String(c)] ?? ''} disabled={readOnly || !(String(c) in form.freespinTriggers.freegame)} aria-label={`Extra spins for ${c} scatters`}
						onchange={(e) => setFrom('freegame', c, Number(e.currentTarget.value))} /></td>
				</tr>
			{/each}
		</tbody>
	</table>
</details>
<SaveBar {dirty} {busy} {error} {ok} onsave={save} disabled={readOnly} />

<style>
	.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px; }
	h3 { margin: 0 0 6px; font-size: 15px; }
	.f { display: grid; grid-template-columns: 1fr 110px; gap: 6px; align-items: center; margin: 3px 0; }
	.small { font-size: 12px; }
	summary { cursor: pointer; margin-top: 10px; }
	table { border-collapse: collapse; }
	td, th { padding: 2px 8px; text-align: left; }
	th { color: var(--muted); font-weight: 600; }
	td input { width: 80px; }
</style>
