<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';

	let { children } = $props();
	const game = $derived(page.params.id as string | undefined);
	const tabs = [
		['', 'Overview'],
		['/setup', 'Setup'],
		['/assets', 'Asset desk'],
		['/preview', 'Preview'],
		['/build', 'Build & package'],
		['/submit', 'Submit'],
	];
</script>

<header>
	<a class="brand" href="/">Stake Game Factory</a>
	{#if game}
		<span class="game">{game}</span>
		<nav>
			{#each tabs as [suffix, label]}
				<a class:active={page.url.pathname === `/game/${game}${suffix}`} href={`/game/${game}${suffix}`}>{label}</a>
			{/each}
		</nav>
	{/if}
</header>

<main>
	{@render children()}
</main>

<style>
	header { display: flex; gap: 18px; align-items: center; padding: 10px 18px; background: #1a1726; border-bottom: 1px solid var(--line); position: sticky; top: 0; z-index: 5; }
	.brand { font-weight: 800; color: var(--text); text-decoration: none; }
	.game { color: var(--accent); font-weight: 700; }
	nav { display: flex; gap: 6px; }
	nav a { color: var(--muted); text-decoration: none; padding: 4px 10px; border-radius: 5px; }
	nav a.active { background: var(--panel); color: var(--text); }
	main { padding: 18px; max-width: 1400px; margin: 0 auto; }
</style>
