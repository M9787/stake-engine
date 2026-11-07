<script lang="ts">
	// Mode cards: name, price, bonus variant, shop texts, math targets with plain explanations, simulation mix.
	// Adding or removing modes is done with a preset (the set of modes decides the reels and quotas).
	import { saveSection, copy, type SaveResult } from './save';
	import SaveBar from './SaveBar.svelte';
	import Rules from './Rules.svelte';

	let {
		game,
		modes,
		targets,
		variants,
		rtp,
		readOnly,
		onsaved,
	}: {
		game: string;
		modes: any[];
		targets: Record<string, any>;
		variants: { id: string }[];
		rtp: number;
		readOnly: boolean;
		onsaved: (r: SaveResult) => void;
	} = $props();

	const initial = () =>
		modes.map((m) => ({
			from: m.name,
			name: m.name,
			kind: m.kind,
			cost: m.cost,
			variant: m.variant,
			label: m.label,
			title: m.title,
			quotas: copy(m.quotas),
			scatterTriggers: copy(m.scatterTriggers),
			target: copy(targets[m.name] ?? {}),
		}));
	let form = $state(initial());
	const start = JSON.stringify(initial());
	let busy = $state(false);
	let error = $state('');
	let ok = $state('');
	const dirty = $derived(JSON.stringify(form) !== start);

	const pct = (v: number) => `${(v * 100).toFixed(2)}%`;
	const parts = (t: any) => (t.wincapRtp ?? 0) + (t.freegameRtp ?? 0) + (t.basegameRtp ?? 0);
	const counts = (m: Record<string, number>) =>
		Object.entries(m)
			.map(([k, v]) => `${k}:${v}`)
			.join(', ');
	function parseCounts(text: string): Record<string, number> | null {
		const out: Record<string, number> = {};
		for (const part of text.split(',').map((x) => x.trim()).filter(Boolean)) {
			const m = /^(\d+)\s*:\s*(\d+)$/.exec(part);
			if (!m) return null;
			out[m[1]] = Number(m[2]);
		}
		return out;
	}
	function setCounts(m: any, k: string, el: HTMLInputElement) {
		const v = parseCounts(el.value);
		if (v) m.scatterTriggers[k] = v;
		else el.value = counts(m.scatterTriggers[k]);
	}
	const QUOTA: Record<string, string> = { wincap: 'Max-win results', freegame: 'Bonus results', zero: 'Losing spins', basegame: 'Normal spins' };
	const TRIG: Record<string, string> = { wincap: 'Max-win results start with', freegame: 'Bonus results start with', all: 'The bonus starts with' };

	function fillBase(t: any) {
		t.basegameRtp = Math.round((rtp - t.wincapRtp - t.freegameRtp) * 10000) / 10000;
	}

	async function save() {
		busy = true;
		error = '';
		ok = '';
		try {
			const r = await saveSection(game, 'modes', { modes: form });
			ok = 'Saved.';
			onsaved(r);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			busy = false;
		}
	}
</script>

<p class="muted small">
	Every mode must return the same share of play to players ({pct(rtp)}): the three shares of each mode must add up to that. Price is in
	multiples of the normal spin. To add or remove a mode, use the Presets tab.
</p>
<div class="cards">
	{#each form as m (m.from)}
		<section class="card panel">
			<h3>{m.kind === 'spin' ? 'Spin mode' : 'Bonus started directly'} <code>{m.from}</code></h3>
			<label class="f"><span>Name (internal)</span><input bind:value={m.name} disabled={readOnly} aria-label={`Mode ${m.from} name`} /></label>
			<label class="f"><span>Button label</span><input bind:value={m.label} disabled={readOnly} aria-label={`Mode ${m.from} label`} /></label>
			<label class="f"><span>Title</span><input bind:value={m.title} disabled={readOnly} aria-label={`Mode ${m.from} title`} /></label>
			<label class="f"><span>Price (x bet)</span><input type="number" step="0.05" min="1" bind:value={m.cost} disabled={readOnly} aria-label={`Mode ${m.from} price`} /></label>
			{#if m.kind === 'buy'}
				<label class="f">
					<span>Bonus kind</span>
					<select bind:value={m.variant} disabled={readOnly} aria-label={`Mode ${m.from} bonus kind`}>
						{#each variants as v}<option value={v.id}>{v.id}</option>{/each}
					</select>
				</label>
			{/if}

			<h4>How it plays</h4>
			{#if m.kind === 'spin'}
				<label class="f">
					<span>Bonus about 1 in</span>
					<input type="number" min="20" max="2000" bind:value={m.target.bonusOneIn} disabled={readOnly} aria-label={`Mode ${m.from} bonus 1 in`} /><em>spins</em>
				</label>
				<label class="f">
					<span>A win about 1 in</span>
					<input type="number" step="0.1" min="1.5" max="50" bind:value={m.target.hitOneIn} disabled={readOnly} aria-label={`Mode ${m.from} hit 1 in`} /><em>spins</em>
				</label>
			{/if}
			<label class="f">
				<span>Share from max wins</span>
				<input type="number" step="0.001" bind:value={m.target.wincapRtp} disabled={readOnly} aria-label={`Mode ${m.from} max-win share`} /><em>{pct(m.target.wincapRtp ?? 0)}</em>
			</label>
			<label class="f">
				<span>Share from bonuses</span>
				<input type="number" step="0.001" bind:value={m.target.freegameRtp} disabled={readOnly} aria-label={`Mode ${m.from} bonus share`} /><em>{pct(m.target.freegameRtp ?? 0)}</em>
			</label>
			{#if m.kind === 'spin'}
				<label class="f">
					<span>Share from normal wins</span>
					<input type="number" step="0.001" bind:value={m.target.basegameRtp} disabled={readOnly} aria-label={`Mode ${m.from} normal share`} /><em>{pct(m.target.basegameRtp ?? 0)}</em>
				</label>
				{#if !readOnly}<button class="secondary small" onclick={() => fillBase(m.target)}>Fill normal-win share so the total is {pct(rtp)}</button>{/if}
				<p class="small muted">
					Average normal win ≈ {((m.target.basegameRtp ?? 0) * (m.target.hitOneIn ?? 0) * m.cost).toFixed(2)}x bet (keep it 2.3 or more, or the math may not settle).
				</p>
			{:else}
				<label class="f">
					<span>Spread low / high</span>
					<input type="number" step="0.5" bind:value={m.target.minM2m} disabled={readOnly} aria-label={`Mode ${m.from} spread low`} />
					<input type="number" step="0.5" bind:value={m.target.maxM2m} disabled={readOnly} aria-label={`Mode ${m.from} spread high`} />
				</label>
			{/if}
			<p class="small" class:bad={Math.abs(parts(m.target) - rtp) > 0.0005} class:ok={Math.abs(parts(m.target) - rtp) <= 0.0005}>
				Total {pct(parts(m.target))} (needs {pct(rtp)})
			</p>

			<details>
				<summary class="muted">Fine tuning (optimizer hints)</summary>
				{#if m.kind === 'spin'}
					<label class="f">
						<span>Lift mid bonus wins</span>
						<input type="number" step="0.5" bind:value={m.target.midWinLift[0]} disabled={readOnly} aria-label={`Mode ${m.from} lift 1`} />
						<input type="number" step="0.5" bind:value={m.target.midWinLift[1]} disabled={readOnly} aria-label={`Mode ${m.from} lift 2`} />
					</label>
					<p class="small muted">Normal-win ranges to push up (factor above 1) or down (below 1):</p>
					<Rules bind:rules={m.target.baseScaling} {readOnly} label={`${m.from} normal-win ranges`} />
				{:else}
					<p class="small muted">Bonus-win ranges to push up (factor above 1) or down (below 1):</p>
					<Rules bind:rules={m.target.scaling} {readOnly} label={`${m.from} bonus-win ranges`} />
				{/if}
			</details>
			<details>
				<summary class="muted">Simulation mix (share of simulated results, not odds)</summary>
				{#each Object.keys(m.quotas) as k}
					<label class="f">
						<span>{QUOTA[k] ?? k}</span>
						<input type="number" step="0.001" min="0" max="1" bind:value={m.quotas[k]} disabled={readOnly} aria-label={`Mode ${m.from} quota ${k}`} />
					</label>
				{/each}
				{#each Object.keys(m.scatterTriggers) as k}
					<label class="f">
						<span>{TRIG[k] ?? k} (scatters:weight)</span>
						<input value={counts(m.scatterTriggers[k])} disabled={readOnly} aria-label={`Mode ${m.from} triggers ${k}`} onchange={(e) => setCounts(m, k, e.currentTarget)} />
					</label>
				{/each}
			</details>
		</section>
	{/each}
</div>
<SaveBar {dirty} {busy} {error} {ok} onsave={save} disabled={readOnly} />

<style>
	.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 10px; }
	.card h3 { margin: 0 0 8px; font-size: 15px; }
	h4 { margin: 10px 0 4px; font-size: 13px; color: var(--muted); }
	.f { display: grid; grid-template-columns: 150px auto auto; gap: 6px; align-items: center; margin: 3px 0; justify-content: start; }
	.f input { width: 110px; }
	.f em { color: var(--muted); font-style: normal; font-size: 12px; }
	.small { font-size: 12px; margin: 4px 0; }
	button.small { padding: 3px 8px; font-size: 12px; }
	summary { cursor: pointer; margin-top: 6px; }
</style>
