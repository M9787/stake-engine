<script lang="ts">
	// Reel strips: download / upload one CSV per strip (one row per stop, one column per reel).
	import { errorText } from '$lib/components/JobPanel.svelte';
	import type { SaveResult } from './save';

	type Strip = { id: string; file: string; reels: number; length: number; symbols: string[]; scatters: number; error?: string };
	let { game, strips, reels, readOnly, onsaved }: { game: string; strips: Strip[]; reels: number; readOnly: boolean; onsaved: (r: SaveResult) => void } = $props();

	const USE: Record<string, string> = {
		BR0: 'Normal spins',
		FR0: 'Bonus spins',
		WCAP: 'Max-win results (bonus)',
	};
	let busy = $state('');
	let error = $state('');
	let ok = $state('');
	const url = (id: string) => `/api/game/${encodeURIComponent(game)}/setup/strip/${encodeURIComponent(id)}`;

	async function upload(id: string, input: HTMLInputElement) {
		const file = input.files?.[0];
		input.value = '';
		if (!file) return;
		busy = id;
		error = '';
		ok = '';
		try {
			const res = await fetch(url(id), { method: 'PUT', headers: { 'content-type': 'text/csv' }, body: await file.text() });
			if (!res.ok) throw new Error(await errorText(res));
			const r = (await res.json()) as SaveResult;
			ok = `${id} replaced with ${file.name}.`;
			onsaved(r);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			busy = '';
		}
	}
</script>

<p class="muted small">
	A reel strip is the loop of symbols each reel spins through: one line per position, {reels} symbols per line (one per reel), separated
	by commas. Download a strip, edit it in a spreadsheet, save as CSV and upload it again. A copy of the old one is kept in the history.
</p>
<table>
	<thead><tr><th>Strip</th><th>Used for</th><th>Size</th><th>Scatters</th><th></th></tr></thead>
	<tbody>
		{#each strips as s (s.id)}
			<tr>
				<td><code>{s.id}</code></td>
				<td>{USE[s.id] ?? 'Custom'}</td>
				<td>{#if s.error}<span class="bad">{s.error}</span>{:else}{s.length} positions × {s.reels} reels{/if}</td>
				<td>{s.scatters}</td>
				<td class="act">
					<a href={url(s.id)} download={s.file}>Download</a>
					{#if !readOnly}
						<label class="up">
							{busy === s.id ? 'Uploading…' : 'Upload CSV'}
							<input type="file" accept=".csv,text/csv" disabled={!!busy} onchange={(e) => upload(s.id, e.currentTarget)} aria-label={`Upload ${s.id}`} />
						</label>
					{/if}
				</td>
			</tr>
		{/each}
	</tbody>
</table>
{#if ok}<p class="ok">{ok}</p>{/if}
{#if error}<p class="bad" role="alert">Could not upload: {error}</p>{/if}

<style>
	table { border-collapse: collapse; width: 100%; }
	th, td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--line); }
	th { color: var(--muted); font-weight: 600; }
	.act { display: flex; gap: 12px; align-items: center; }
	.up { cursor: pointer; color: var(--accent); }
	.up input { display: none; }
	.small { font-size: 12px; }
</style>
