<script lang="ts">
	import type { Issue, ValidateResult } from '$lib/types';

	let { result, okText = 'Everything checks out.' }: { result: ValidateResult | null; okText?: string } = $props();

	const SECTION: Record<string, string> = {
		identity: 'Game name and version',
		theme: 'Colours',
		texts: 'Texts',
		text: 'Texts',
		modes: 'Bet modes',
		math: 'Math settings',
		board: 'Board',
		symbols: 'Symbols',
		paytable: 'Paytable',
		reels: 'Reels',
		features: 'Features',
		presentation: 'Presentation',
		assets: 'Art and sound',
	};
	const FIELD: Record<string, string> = {
		displayName: 'display name',
		version: 'version',
		gameId: 'game id',
		palette: 'palette',
		ui: 'interface',
		text: 'text colour',
		heading: 'heading colour',
		rule: 'line colour',
	};

	/** "theme.palette.antique_gold" -> "Colours › palette › antique gold" */
	function label(path: string): string {
		if (!path) return 'Whole game';
		const parts = path.replace(/\[(\d+)\]/g, '.$1').split(/[./]/).filter(Boolean);
		const [head, ...rest] = parts;
		if ((head === 'texts' || head === 'text') && rest.length) return `Text “${rest.join('.')}”`;
		const out = [SECTION[head] ?? head.replace(/_/g, ' ')];
		for (const p of rest) out.push(/^\d+$/.test(p) ? `#${Number(p) + 1}` : (FIELD[p] ?? p.replace(/_/g, ' ')));
		return out.join(' › ');
	}
</script>

{#snippet list(items: Issue[], kind: 'bad' | 'warn')}
	<ul class="issues {kind}">
		{#each items as it}
			<li><span class="where">{label(it.path)}</span> <span>{it.message}</span></li>
		{/each}
	</ul>
{/snippet}

{#if result}
	<div class="box" role="status">
		{#if result.errors.length === 0 && result.warnings.length === 0}
			<p class="ok">✔ {okText}</p>
		{/if}
		{#if result.errors.length}
			<p class="bad"><strong>{result.errors.length} problem{result.errors.length === 1 ? '' : 's'} to fix</strong> before this game can be built:</p>
			{@render list(result.errors, 'bad')}
		{/if}
		{#if result.warnings.length}
			<p class="warn"><strong>{result.warnings.length} thing{result.warnings.length === 1 ? '' : 's'} to look at</strong> (not blocking):</p>
			{@render list(result.warnings, 'warn')}
		{/if}
	</div>
{/if}

<style>
	.box { display: flex; flex-direction: column; gap: 4px; }
	p { margin: 4px 0; }
	ul { margin: 0 0 6px; padding-left: 18px; }
	li { margin: 2px 0; }
	.where { font-weight: 700; }
	ul.bad .where { color: var(--bad); }
	ul.warn .where { color: var(--warn); }
</style>
