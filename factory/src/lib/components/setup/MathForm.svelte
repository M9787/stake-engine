<script lang="ts">
	// Math basics: return to player, max win, simulations per mode.
	import { saveSection, type SaveResult } from './save';
	import SaveBar from './SaveBar.svelte';

	let { game, math, modes, readOnly, onsaved }: { game: string; math: any; modes: { name: string }[]; readOnly: boolean; onsaved: (r: SaveResult) => void } = $props();

	const initial = () => ({ rtp: math.rtp, wincap: math.wincap, sims: Object.fromEntries(modes.map((m) => [m.name, math.sims[m.name] ?? 100000])) });
	let form = $state(initial());
	const start = JSON.stringify(initial());
	let busy = $state(false);
	let error = $state('');
	let ok = $state('');
	const dirty = $derived(JSON.stringify(form) !== start);
	const rtpPct = $derived(Math.round(form.rtp * 100000) / 1000);

	async function save() {
		busy = true;
		error = '';
		ok = '';
		try {
			const r = await saveSection(game, 'math', { math: form });
			ok = 'Saved.';
			onsaved(r);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			busy = false;
		}
	}
</script>

<label class="f">
	<span>Return to player</span>
	<input type="number" step="0.001" min="0.96" max="0.967" bind:value={form.rtp} disabled={readOnly} aria-label="Return to player" />
	<em>{rtpPct}% of all play comes back to players over time (Stake allows 96.0–96.7%). If you change it, update each mode's shares too.</em>
</label>
<label class="f">
	<span>Max win (x bet)</span>
	<input type="number" min="100" max="1000000" bind:value={form.wincap} disabled={readOnly} aria-label="Max win" />
	<em>The biggest win one spin can pay. Above 100,000x Stake lowers its limits for the game.</em>
</label>
<h3>Simulated spins per mode</h3>
<p class="muted small">More spins make the final math more exact but take longer. The quick preview always uses 10,000.</p>
{#each modes as m (m.name)}
	<label class="f">
		<span><code>{m.name}</code></span>
		<input type="number" step="10000" min="10000" max="1000000" bind:value={form.sims[m.name]} disabled={readOnly} aria-label={`Simulations for ${m.name}`} />
	</label>
{/each}
<SaveBar {dirty} {busy} {error} {ok} onsave={save} disabled={readOnly} />

<style>
	.f { display: grid; grid-template-columns: 160px 130px 1fr; gap: 8px; align-items: center; margin: 5px 0; }
	.f em { color: var(--muted); font-style: normal; font-size: 12px; }
	h3 { font-size: 14px; margin: 14px 0 4px; }
	.small { font-size: 12px; }
</style>
