<script lang="ts">
	// Symbol roster: display names (text/en.json) and the tier of pay symbols. Ids and roles come from presets.
	import { saveSection, copy, type SaveResult } from './save';
	import SaveBar from './SaveBar.svelte';

	type Sym = { id: string; role: 'pay' | 'scatter' | 'wild'; tier?: 'high' | 'low'; nameKey: string; name: string };
	let { game, symbols, readOnly, onsaved }: { game: string; symbols: Sym[]; readOnly: boolean; onsaved: (r: SaveResult) => void } = $props();

	let form = $state(copy(symbols));
	let busy = $state(false);
	let error = $state('');
	let ok = $state('');
	const dirty = $derived(JSON.stringify(form) !== JSON.stringify(symbols));
	const ROLE: Record<string, string> = { pay: 'Pays in clusters', scatter: 'Scatter (starts the bonus)', wild: 'Wild (joins any cluster)' };

	async function save() {
		busy = true;
		error = '';
		ok = '';
		try {
			const r = await saveSection(game, 'symbols', { symbols: form.map((s) => ({ id: s.id, role: s.role, tier: s.tier, name: s.name })) });
			ok = 'Saved.';
			onsaved(r);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			busy = false;
		}
	}
</script>

<p class="muted small">The name is what players see in the rules. High symbols are the rare, valuable ones; low symbols are common and pay less.</p>
<table>
	<thead><tr><th>Symbol</th><th>Name players see</th><th>What it does</th><th>Value group</th></tr></thead>
	<tbody>
		{#each form as s (s.id)}
			<tr>
				<td><code>{s.id}</code></td>
				<td><input bind:value={s.name} disabled={readOnly} aria-label={`Name of ${s.id}`} maxlength="40" /></td>
				<td class="muted">{ROLE[s.role] ?? s.role}</td>
				<td>
					{#if s.role === 'pay'}
						<select bind:value={s.tier} disabled={readOnly} aria-label={`Value group of ${s.id}`}>
							<option value="high">High</option>
							<option value="low">Low</option>
						</select>
					{:else}<span class="muted">—</span>{/if}
				</td>
			</tr>
		{/each}
	</tbody>
</table>
<SaveBar {dirty} {busy} {error} {ok} onsave={save} disabled={readOnly} />

<style>
	table { border-collapse: collapse; width: 100%; }
	th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--line); }
	th { color: var(--muted); font-weight: 600; }
	.small { font-size: 12px; }
</style>
