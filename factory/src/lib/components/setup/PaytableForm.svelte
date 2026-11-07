<script lang="ts">
	// Paytable grid: cluster-size bands (columns) x pay symbols (rows), wins in x bet. minPay is computed.
	import { saveSection, copy, type SaveResult } from './save';
	import SaveBar from './SaveBar.svelte';

	type Paytable = { bands: [number, number][]; pays: Record<string, number[]>; minPay: number };
	let { game, paytable, payIds, cells, readOnly, onsaved }: { game: string; paytable: Paytable; payIds: string[]; cells: number; readOnly: boolean; onsaved: (r: SaveResult) => void } = $props();

	let form = $state(copy(paytable));
	let busy = $state(false);
	let error = $state('');
	let ok = $state('');
	const dirty = $derived(JSON.stringify(form) !== JSON.stringify(paytable));
	const minPay = $derived(Math.min(...payIds.flatMap((id) => form.pays[id] ?? []).filter((v) => typeof v === 'number')));

	function addBand() {
		const last = form.bands[form.bands.length - 1];
		const mid = Math.max(last[0], Math.min(last[1] - 1, last[0] + 3));
		form.bands.splice(form.bands.length - 1, 1, [last[0], mid], [mid + 1, last[1]]);
		for (const id of payIds) form.pays[id].push(form.pays[id][form.pays[id].length - 1]);
	}
	function removeBand() {
		if (form.bands.length < 2) return;
		const last = form.bands.pop()!;
		form.bands[form.bands.length - 1][1] = last[1];
		for (const id of payIds) form.pays[id].pop();
	}

	async function save() {
		busy = true;
		error = '';
		ok = '';
		try {
			const r = await saveSection(game, 'paytable', { paytable: { bands: form.bands, pays: form.pays } });
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
	Each column is a cluster size (how many touching symbols). Values are wins in multiples of the bet. The bands must follow each other
	without gaps, and the last one must end at {cells} (every cell of the board). Smallest win now: <strong>{minPay}x</strong>.
</p>
<div class="scroll">
	<table>
		<thead>
			<tr>
				<th>Symbol</th>
				{#each form.bands as b, i}
					<th>
						<span class="band">
							<input type="number" min="2" max={cells} bind:value={b[0]} disabled={readOnly} aria-label={`Band ${i + 1} from`} />–<input
								type="number" min="2" max={cells} bind:value={b[1]} disabled={readOnly} aria-label={`Band ${i + 1} to`} />
						</span>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each payIds as id (id)}
				<tr>
					<td><code>{id}</code></td>
					{#each form.pays[id] as _, i}
						<td><input type="number" step="0.1" min="0.01" bind:value={form.pays[id][i]} disabled={readOnly} aria-label={`${id} win for band ${i + 1}`} /></td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>
{#if !readOnly}
	<div class="row">
		<button class="secondary" onclick={addBand} disabled={form.bands.length >= 8}>Split last band</button>
		<button class="secondary" onclick={removeBand} disabled={form.bands.length < 2}>Merge last two bands</button>
	</div>
{/if}
<SaveBar {dirty} {busy} {error} {ok} onsave={save} disabled={readOnly} />

<style>
	.scroll { overflow-x: auto; }
	table { border-collapse: collapse; }
	th, td { padding: 4px 6px; border-bottom: 1px solid var(--line); text-align: left; }
	th { color: var(--muted); font-weight: 600; }
	input[type='number'] { width: 76px; }
	.band input { width: 52px; }
	.row { display: flex; gap: 8px; margin-top: 8px; }
	.small { font-size: 12px; }
</style>
