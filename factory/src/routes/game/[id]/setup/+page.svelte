<script lang="ts">
	// Game setup (factory v2): Presets (one form -> apply_preset job) and Advanced (direct edits per section).
	// Server: src/lib/server/setup.ts, API /api/game/[id]/setup, /setup/preset, /setup/strip/[strip], /math-state.
	import { page } from '$app/state';
	import type { MathState, ValidateResult } from '$lib/types';
	import { api } from '$lib/components/JobPanel.svelte';
	import Issues from '$lib/components/Issues.svelte';
	import PresetForm from '$lib/components/setup/PresetForm.svelte';
	import SymbolsForm from '$lib/components/setup/SymbolsForm.svelte';
	import PaytableForm from '$lib/components/setup/PaytableForm.svelte';
	import ModesForm from '$lib/components/setup/ModesForm.svelte';
	import FeaturesForm from '$lib/components/setup/FeaturesForm.svelte';
	import StripsForm from '$lib/components/setup/StripsForm.svelte';
	import MathForm from '$lib/components/setup/MathForm.svelte';
	import ReviewForm from '$lib/components/setup/ReviewForm.svelte';
	import type { SaveResult } from '$lib/components/setup/save';

	const id = $derived(page.params.id as string);

	let setup = $state<any>(null);
	let loadError = $state('');
	let version = $state(0); // re-keys the forms after every reload
	let validation = $state<ValidateResult | null>(null);
	let math = $state<MathState | null>(null);
	let tab = $state<'presets' | 'advanced'>('presets');
	let part = $state('symbols');
	let lastSnapshot = $state('');

	const PARTS: [string, string][] = [
		['symbols', 'Symbols'],
		['paytable', 'Paytable'],
		['modes', 'Modes'],
		['features', 'Features'],
		['strips', 'Reel strips'],
		['math', 'Math'],
		['review', 'Review & listing'],
	];
	const TIER: Record<string, string> = {
		none: 'No math has been run for this game yet.',
		preview: 'Last math run: quick preview (an estimate, not for release).',
		candidate: 'Last math run: full run.',
		frozen: 'Math is frozen: the approved weights are kept.',
	};

	const readOnly = $derived(!!setup?.frozen);
	const cells = $derived(setup ? setup.board.reels * setup.board.rows : 0);
	const payIds = $derived(setup ? setup.symbols.filter((s: any) => s.role === 'pay').map((s: any) => s.id) : []);
	const current = $derived.by(() => {
		if (!setup) return null;
		const base = setup.modes.find((m: any) => m.kind === 'spin' && m.cost === 1);
		const kinds = ['base'];
		if (setup.modes.some((m: any) => m.kind === 'spin' && m.cost > 1)) kinds.push('ante');
		if (setup.modes.some((m: any) => m.kind === 'buy')) kinds.push('buy');
		return {
			board: `${setup.board.reels}x${setup.board.rows}`,
			modes: kinds,
			wincap: setup.math.wincap,
			bonusOneIn: (base && setup.math.targets[base.name]?.bonusOneIn) ?? 400,
		};
	});

	async function load() {
		loadError = '';
		try {
			setup = await api<any>(`/api/game/${encodeURIComponent(id)}/setup`);
			version++;
		} catch (e) {
			loadError = (e as Error).message;
		}
		api<MathState>(`/api/game/${encodeURIComponent(id)}/math-state`)
			.then((m) => (math = m))
			.catch(() => (math = null));
	}

	async function check() {
		validation = await api<ValidateResult>(`/api/game/${encodeURIComponent(id)}/validate`).catch(() => null);
	}

	function saved(r: SaveResult) {
		validation = r.validation;
		lastSnapshot = r.snapshot ?? '';
		load();
	}

	$effect(() => {
		void id;
		setup = null;
		validation = null;
		load();
		check();
	});
</script>

<svelte:head><title>{id} · Setup</title></svelte:head>

<h1>Game setup</h1>
{#if loadError}
	<div class="errbox" role="alert">Could not open this game. {loadError}</div>
{:else if !setup}
	<p class="muted">Loading…</p>
{:else}
	{#if readOnly}
		<div class="notice" role="note">
			<strong>Approved game.</strong> Its board, symbols, paytable, modes and math are frozen and shown read-only. Only the review and listing texts can change.
		</div>
	{/if}
	<div class="state panel" role="status">
		<span>
			<strong>{setup.board.reels}×{setup.board.rows}</strong> board · {setup.modes.length} mode{setup.modes.length === 1 ? '' : 's'} · max win {setup.math.wincap.toLocaleString()}x
		</span>
		{#if math}
			<span class="muted">{TIER[math.tier] ?? math.tier}</span>
			{#if math.stale && math.tier !== 'none'}
				<span class="warn">The math settings changed since that run: run the math again on the <a href={`/game/${id}/build`}>Build page</a>.</span>
			{/if}
		{/if}
		{#if lastSnapshot}<span class="muted">Saved (a copy of the previous version is in the history).</span>{/if}
	</div>

	<div class="tabs" role="tablist">
		<button role="tab" aria-selected={tab === 'presets'} class:active={tab === 'presets'} onclick={() => (tab = 'presets')}>Presets</button>
		<button role="tab" aria-selected={tab === 'advanced'} class:active={tab === 'advanced'} onclick={() => (tab = 'advanced')}>Advanced</button>
	</div>

	{#if validation}
		<div class="panel issues"><Issues result={validation} okText="The game definition checks out." /></div>
	{/if}

	{#if tab === 'presets'}
		<p class="muted">Pick a few simple choices and the factory writes the whole game setup for you. You can fine-tune it afterwards in Advanced.</p>
		{#if current}
			{#key id}
				<PresetForm
					game={id}
					boards={setup.presets.boards}
					volatility={setup.presets.volatility}
					{current}
					{readOnly}
					ondone={() => {
						load();
						check();
					}}
				/>
			{/key}
		{/if}
	{:else}
		<nav class="parts" aria-label="Advanced sections">
			{#each PARTS as [k, label]}
				<button class="secondary" class:active={part === k} aria-pressed={part === k} onclick={() => (part = k)}>{label}</button>
			{/each}
		</nav>
		<section class="panel">
			{#key `${version}-${part}`}
				{#if part === 'symbols'}
					<SymbolsForm game={id} symbols={setup.symbols} {readOnly} onsaved={saved} />
				{:else if part === 'paytable'}
					<PaytableForm game={id} paytable={setup.paytable} {payIds} {cells} {readOnly} onsaved={saved} />
				{:else if part === 'modes'}
					<ModesForm game={id} modes={setup.modes} targets={setup.math.targets} variants={setup.features.bonusVariants} rtp={setup.math.rtp} {readOnly} onsaved={saved} />
				{:else if part === 'features'}
					<FeaturesForm game={id} features={setup.features} freespinTriggers={setup.freespinTriggers} {cells} {readOnly} onsaved={saved} />
				{:else if part === 'strips'}
					<StripsForm game={id} strips={setup.strips} reels={setup.board.reels} {readOnly} onsaved={saved} />
				{:else if part === 'math'}
					<MathForm game={id} math={setup.math} modes={setup.modes} {readOnly} onsaved={saved} />
				{:else if part === 'review'}
					<ReviewForm game={id} review={setup.review} listing={setup.listing} onsaved={saved} />
				{/if}
			{/key}
		</section>
	{/if}
{/if}

<style>
	.notice { background: #2e2814; border: 1px solid var(--accent); border-radius: 6px; padding: 8px 10px; margin-bottom: 12px; }
	.errbox { background: #3a1714; border: 1px solid var(--bad); color: #ffd9d4; border-radius: 6px; padding: 8px 10px; margin: 8px 0; }
	.state { display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: center; margin-bottom: 12px; }
	.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--line); margin-bottom: 12px; }
	.tabs button { background: transparent; color: var(--muted); border-radius: 6px 6px 0 0; padding: 8px 16px; }
	.tabs button.active { background: var(--panel); color: var(--text); border: 1px solid var(--line); border-bottom-color: var(--panel); margin-bottom: -1px; }
	.issues { margin-bottom: 12px; }
	.parts { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
	.parts button.active { background: var(--accent); color: #1b1446; }
</style>
