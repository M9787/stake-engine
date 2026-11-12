<script lang="ts">
	// Stake approval checklist (preview): build/<id>/reports/stake_checklist.json via GET /api/game/[id]/checklist.
	// Items and their checks: core/stake_checklist.v1.json, tools/release/checklist.py.
	import type { ChecklistItem, StakeChecklist } from '$lib/types';
	import JobPanel, { api } from '$lib/components/JobPanel.svelte';

	let { game }: { game: string } = $props();

	let list = $state<StakeChecklist | null>(null);
	let listError = $state('');
	let only = $state(false); // show only fail / look / unknown

	const ORDER = ['math', 'frontend', 'replay', 'social', 'rules', 'ui', 'quality', 'ip', 'tiles', 'general'];
	const ICON: Record<ChecklistItem['status'], string> = { pass: '✔', fail: '✘', manual: '☐', unknown: '?' };
	const WORD: Record<ChecklistItem['status'], string> = { pass: 'pass', fail: 'fail', manual: 'look', unknown: 'no evidence' };

	const groups = $derived.by(() => {
		if (!list) return [];
		const names = [...ORDER, ...new Set(list.items.map((i) => i.group).filter((g) => !ORDER.includes(g)))];
		return names
			.map((name) => {
				const all = list!.items.filter((i) => i.group === name);
				return { name, all, shown: only ? all.filter((i) => i.status !== 'pass') : all };
			})
			.filter((g) => g.all.length);
	});

	async function load() {
		listError = '';
		try {
			list = await api<StakeChecklist>(`/api/game/${encodeURIComponent(game)}/checklist`);
		} catch (e) {
			list = null;
			listError = (e as Error).message;
		}
	}

	$effect(() => {
		if (game) load();
	});
</script>

<div class="panel">
	<h2>Stake approval checklist (preview)</h2>
	<p class="muted small">
		Every Stake review item for this game. Green items were checked from the files and test runs; boxes are for you to
		look at by hand (each says what to look at). Stake's three reviewers then rate 0–3 stars each; the game needs 6 of 9
		points.
	</p>
	<JobPanel {game} tool="checklist" label="Run checklist" ondone={load} />

	{#if !list}
		<p class="muted">{listError || 'Loading…'}</p>
	{:else}
		<p class="summary">
			<span class="ok">{list.summary.pass} pass</span> ·
			<span class="bad">{list.summary.fail} fail</span> ·
			<span>{list.summary.manual} to look at</span> ·
			<span class="muted">{list.summary.unknown} without evidence</span>
			<span class="muted small">({list.mode} mode, made {list.generated})</span>
			<label class="small"><input type="checkbox" bind:checked={only} /> hide passed items</label>
		</p>
		{#each groups as g}
			{@const fails = g.all.filter((i) => i.status === 'fail').length}
			<details open={fails > 0 || only}>
				<summary>
					<strong>{g.name}</strong>
					<span class="muted small">{g.all.filter((i) => i.status === 'pass').length}/{g.all.length} pass</span>
					{#if fails}<span class="bad small">{fails} fail</span>{/if}
				</summary>
				<ul>
					{#each g.shown as it}
						<li class={it.status}>
							<span class="icon" title={WORD[it.status]}>{ICON[it.status]}</span>
							<span class="id">{it.id}</span>
							<span class="body">
								<span>{it.text}</span>
								<span class="muted small">
									{WORD[it.status]} · {it.verify} · {it.evidence}
									{#if it.source?.startsWith('http')} · <a href={it.source} target="_blank" rel="noopener">source</a>{/if}
								</span>
							</span>
						</li>
					{/each}
				</ul>
			</details>
		{/each}
	{/if}
</div>

<style>
	h2 { margin-top: 0; }
	.small { font-size: 13px; }
	.summary { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
	details { border-top: 1px solid var(--line); padding: 6px 0; }
	summary { cursor: pointer; display: flex; gap: 10px; align-items: baseline; text-transform: capitalize; }
	ul { list-style: none; padding: 0; margin: 6px 0; display: flex; flex-direction: column; gap: 4px; }
	li { display: grid; grid-template-columns: 22px 150px 1fr; gap: 8px; align-items: start; padding: 4px 6px; border-radius: 5px; }
	li.fail { background: #3a1714; }
	li.unknown { background: #2a2638; }
	.icon { font-weight: 700; text-align: center; }
	li.pass .icon { color: var(--ok); }
	li.fail .icon { color: var(--bad); }
	li.manual .icon { color: var(--warn); }
	.id { font-family: monospace; font-size: 12px; word-break: break-all; }
	.body { display: flex; flex-direction: column; gap: 2px; }
</style>
