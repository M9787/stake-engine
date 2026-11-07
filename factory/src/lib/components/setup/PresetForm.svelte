<script lang="ts">
	// Presets: board, volatility, max win, bonus frequency, modes -> apply_preset job (tools/gamedef/apply_preset.py).
	// The server snapshots the skin, then starts the job; this form follows it with JobPanel (attach).
	import type { Job, PresetRequest } from '$lib/types';
	import JobPanel, { api, sendJson } from '$lib/components/JobPanel.svelte';

	type Vol = { id: 'low' | 'medium' | 'high'; label: string; explain: string; defaults: { wincap: number; bonusOneIn: number } };
	let {
		game,
		boards,
		volatility,
		current,
		readOnly,
		ondone,
	}: {
		game: string;
		boards: string[];
		volatility: Vol[];
		current: { board: string; modes: string[]; wincap: number; bonusOneIn: number };
		readOnly: boolean;
		ondone: (job: Job) => void;
	} = $props();

	let form = $state<PresetRequest>({ board: current.board, volatility: 'medium', wincap: current.wincap, bonusOneIn: current.bonusOneIn, modes: [...current.modes] });
	let jobId = $state('');
	let error = $state('');
	let starting = $state(false);

	const square = $derived(boards.filter((b) => b.split('x')[0] === b.split('x')[1]));
	const other = $derived(boards.filter((b) => b.split('x')[0] !== b.split('x')[1]));
	const MODES: { id: string; label: string; help: string }[] = [
		{ id: 'base', label: 'Normal spin (1x)', help: 'Always included.' },
		{ id: 'ante', label: 'Boosted spin (1.25x)', help: 'Costs a bit more per spin, bonus comes more often.' },
		{ id: 'buy', label: 'Start the bonus directly (100x)', help: 'Players pay 100x the bet to start the bonus at once.' },
	];

	function pickVol(v: Vol) {
		form.volatility = v.id;
		form.wincap = v.defaults.wincap;
		form.bonusOneIn = v.defaults.bonusOneIn;
	}
	function toggle(id: string, on: boolean) {
		form.modes = MODES.map((m) => m.id).filter((m) => m === 'base' || (m === id ? on : form.modes.includes(m)));
	}

	async function apply() {
		if (!window.confirm('This replaces the board, symbols, paytable, reel strips, modes and math of this game. A copy of the current version is kept in the history. Continue?'))
			return;
		starting = true;
		error = '';
		try {
			const r = await api<{ job: Job; snapshot: string }>(`/api/game/${encodeURIComponent(game)}/setup/preset`, sendJson('POST', { preset: $state.snapshot(form) }));
			jobId = r.job.id;
		} catch (e) {
			error = (e as Error).message;
		} finally {
			starting = false;
		}
	}
</script>

<div class="grid">
	<section class="panel">
		<h3>1. Board</h3>
		<p class="muted small">Reels across × rows down. Bigger boards mean bigger clusters.</p>
		<select bind:value={form.board} disabled={readOnly} aria-label="Board size">
			<optgroup label="Square">
				{#each square as b}<option value={b}>{b}</option>{/each}
			</optgroup>
			<optgroup label="Other shapes">
				{#each other as b}<option value={b}>{b}</option>{/each}
			</optgroup>
		</select>
	</section>

	<section class="panel">
		<h3>2. How wild should it feel?</h3>
		{#each volatility as v (v.id)}
			<label class="radio">
				<input type="radio" name="vol" checked={form.volatility === v.id} onchange={() => pickVol(v)} disabled={readOnly} />
				<span><strong>{v.label}</strong> <span class="muted">{v.explain}</span></span>
			</label>
		{/each}
	</section>

	<section class="panel">
		<h3>3. Big numbers</h3>
		<label class="f">
			<span>Max win</span>
			<input type="number" min="100" max="1000000" step="100" bind:value={form.wincap} disabled={readOnly} aria-label="Max win" /><em>x bet</em>
		</label>
		<label class="f">
			<span>Bonus about 1 in</span>
			<input type="number" min="20" max="2000" step="10" bind:value={form.bonusOneIn} disabled={readOnly} aria-label="Bonus 1 in" /><em>spins</em>
		</label>
		<p class="muted small">Picking a feel above fills in typical values; you can change them.</p>
	</section>

	<section class="panel">
		<h3>4. Ways to play</h3>
		{#each MODES as m (m.id)}
			<label class="radio">
				<input type="checkbox" checked={form.modes.includes(m.id)} disabled={readOnly || m.id === 'base'} onchange={(e) => toggle(m.id, e.currentTarget.checked)} aria-label={m.label} />
				<span><strong>{m.label}</strong> <span class="muted">{m.help}</span></span>
			</label>
		{/each}
	</section>
</div>

<div class="apply">
	<button onclick={apply} disabled={readOnly || starting}>{starting ? 'Starting…' : 'Apply preset'}</button>
	<span class="muted small">Writes the game files, then checks them. Run the math afterwards on the Build page.</span>
</div>
{#if error}<div class="errbox" role="alert">{error}</div>{/if}
{#if jobId}
	<JobPanel {game} tool="apply_preset" label="Preset run" attach={jobId} disabled disabledNote="" {ondone} />
{/if}

<style>
	.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; }
	h3 { margin: 0 0 6px; font-size: 15px; }
	.radio { display: flex; gap: 8px; align-items: flex-start; margin: 6px 0; cursor: pointer; }
	.f { display: grid; grid-template-columns: 130px 120px auto; gap: 6px; align-items: center; margin: 4px 0; }
	.f em { color: var(--muted); font-style: normal; }
	.small { font-size: 12px; }
	.apply { display: flex; gap: 12px; align-items: center; margin: 12px 0; }
	.errbox { background: #3a1714; border: 1px solid var(--bad); color: #ffd9d4; border-radius: 6px; padding: 8px 10px; margin: 8px 0; }
</style>
