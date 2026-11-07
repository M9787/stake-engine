<script lang="ts">
	// Editor for optimizer hint rules [[from, to], factor] (win ranges in x bet).
	let { rules = $bindable(), readOnly, label }: { rules: [[number, number], number][]; readOnly: boolean; label: string } = $props();
</script>

<table class="rules" aria-label={label}>
	<thead><tr><th>Wins from (x)</th><th>to (x)</th><th>Push factor</th><th></th></tr></thead>
	<tbody>
		{#each rules as r, i}
			<tr>
				<td><input type="number" bind:value={r[0][0]} disabled={readOnly} aria-label={`${label} ${i + 1} from`} /></td>
				<td><input type="number" bind:value={r[0][1]} disabled={readOnly} aria-label={`${label} ${i + 1} to`} /></td>
				<td><input type="number" step="0.1" bind:value={r[1]} disabled={readOnly} aria-label={`${label} ${i + 1} factor`} /></td>
				<td>{#if !readOnly}<button class="secondary" onclick={() => rules.splice(i, 1)} aria-label={`Remove ${label} ${i + 1}`}>✕</button>{/if}</td>
			</tr>
		{/each}
	</tbody>
</table>
{#if !readOnly}<button class="secondary" onclick={() => rules.push([[1, 2], 1])}>Add range</button>{/if}

<style>
	.rules { border-collapse: collapse; margin: 4px 0; }
	.rules td, .rules th { padding: 2px 4px; text-align: left; }
	.rules th { color: var(--muted); font-weight: 600; font-size: 12px; }
	input { width: 90px; }
</style>
