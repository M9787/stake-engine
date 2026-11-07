<script lang="ts">
	// Asset desk (docs/10 plan v3.3 sections 12 [P2 P5 P6 P8], 13, 14): every slot of one game grouped by
	// sitting. The tools do the work (ingest.py, contact_sheet.py); this page only shows and uploads.
	import { page } from '$app/state';
	import JobPanel, { api, sendJson } from '$lib/components/JobPanel.svelte';
	import AssetCard from '$lib/components/assets/AssetCard.svelte';
	import type { Desk, DeskCard } from '$lib/components/assets/desk';

	const game = $derived(page.params.id as string);
	let desk = $state<Desk | null>(null);
	let loadError = $state('');
	let loading = $state(false);
	let version = $state(Date.now());
	let contactVersion = $state(0);
	let signer = $state('');
	let minutesError = $state('');

	async function load() {
		loading = true;
		loadError = '';
		try {
			desk = await api<Desk>(`/api/game/${encodeURIComponent(game)}/assets`);
			version = Date.now();
			if (desk.contact.length && !contactVersion) contactVersion = Date.now();
		} catch (e) {
			loadError = (e as Error).message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (game) load();
	});

	function replaceCard(c: DeskCard) {
		if (!desk) return;
		const i = desk.slots.findIndex((x) => x.id === c.id);
		if (i >= 0) desk.slots[i] = c;
		version = Date.now();
		// the required count and Suno counter come from the whole desk: refresh quietly
		api<Desk>(`/api/game/${encodeURIComponent(game)}/assets`).then((d) => {
			if (desk) {
				desk.required = d.required;
				desk.suno = d.suno;
				desk.signoff = d.signoff;
				desk.unknownFiles = d.unknownFiles;
			}
		}).catch(() => {});
	}

	const locked = (c: DeskCard) => !!desk && !desk.sref && c.kind === 'image' && c.id !== 'hero';
	const minutesTotal = $derived(desk ? Object.values(desk.minutesLogged).reduce((a, b) => a + b, 0) : 0);
	const bySitting = $derived(
		desk ? desk.sittings.map((s) => ({ ...s, slots: desk!.slots.filter((c) => c.sitting === s.id) })).filter((s) => s.slots.length) : [],
	);

	let srefError = $state('');
	async function saveSref(value: string) {
		srefError = '';
		try {
			await api(`/api/game/${encodeURIComponent(game)}/assets/style`, sendJson('PUT', { sref: value.trim() || null }));
			await load(); // prompts change (--sref is appended), slots unlock
		} catch (e) {
			srefError = (e as Error).message;
		}
	}

	async function saveMinutes(sitting: number, value: string) {
		minutesError = '';
		const minutes = Number(value || 0);
		if (!Number.isFinite(minutes) || minutes < 0) {
			minutesError = 'Minutes must be a number.';
			return;
		}
		try {
			await api(`/api/game/${encodeURIComponent(game)}/assets/provenance`, sendJson('PUT', { sitting, minutes }));
			if (desk) desk.minutesLogged = { ...desk.minutesLogged, [String(sitting)]: minutes };
		} catch (e) {
			minutesError = (e as Error).message;
		}
	}
</script>

<svelte:head><title>Asset desk · {game}</title></svelte:head>

<h1>Asset desk</h1>

{#if loadError}
	<div class="panel bad" role="alert">{loadError} <button class="secondary" onclick={load}>Try again</button></div>
{:else if !desk}
	<p class="muted">Loading the slots (renders the prompts and checks your files)…</p>
{:else}
	<section class="summary panel" aria-label="Progress">
		<div>
			<strong class:ok={desk.required.filled === desk.required.total}>{desk.required.filled}/{desk.required.total}</strong>
			<span class="muted">required slots complete</span>
			<progress max={desk.required.total || 1} value={desk.required.filled}></progress>
		</div>
		<div><strong>{minutesTotal}</strong> <span class="muted">minutes logged</span></div>
		<div>
			<strong>{desk.suno.have}/{desk.suno.needed}</strong>
			<span class="muted">Suno downloads{#if desk.suno.limit} (plan limit {desk.suno.limit}/month){/if}</span>
		</div>
		<div>
			{#if desk.sref}
				<span class="ok">Style reference set</span>
			{:else}
				<span class="warn">No style reference yet: make the hero first (sitting 1)</span>
			{/if}
			<label class="sref">
				<span class="muted">Hero image link (style reference)</span>
				<input
					value={desk.sref ?? ''}
					placeholder="https://… (Midjourney: right-click the picked hero, Copy image address)"
					onchange={(e) => saveSref((e.currentTarget as HTMLInputElement).value)}
				/>
			</label>
			{#if srefError}<span class="bad">{srefError}</span>{/if}
		</div>
		<div>
			{#if desk.signoff}
				<span class={desk.signoff.current ? 'ok' : 'warn'}>
					Signed by {desk.signoff.signedBy} on {desk.signoff.date}{desk.signoff.current ? '' : ' (files changed since: sign again)'}
				</span>
			{:else}
				<span class="muted">Not signed off yet</span>
			{/if}
		</div>
		<button class="secondary" onclick={load} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</button>
	</section>

	{#if desk.unknownFiles.length}
		<div class="panel warn">
			These files have a name the desk does not know (rename them to a slot id, or upload them on the right card):
			<ul>{#each desk.unknownFiles as f}<li>{f}</li>{/each}</ul>
		</div>
	{/if}

	{#each bySitting as s (s.id)}
		{@const done = s.slots.filter((c) => c.complete).length}
		<section class="sitting" aria-labelledby={`sit-${s.id}`}>
			<div class="sithead">
				<h2 id={`sit-${s.id}`}>Sitting {s.id}: {s.title} <span class="muted">(about {s.minutes} min)</span></h2>
				<progress max={s.slots.length} value={done}></progress>
				<span class="muted">{done}/{s.slots.length} complete</span>
				<label class="muted mins">minutes spent
					<input type="number" min="0" step="5" value={desk.minutesLogged[String(s.id)] ?? ''} onblur={(e) => saveMinutes(s.id, (e.currentTarget as HTMLInputElement).value)} />
				</label>
			</div>
			<p class="muted note">{s.note}</p>
			<div class="grid">
				{#each s.slots as c (c.id)}
					<AssetCard {game} card={c} licences={desk.licences} locked={locked(c)} {version} onchange={replaceCard} oningested={load} />
				{/each}
			</div>
		</section>
	{/each}
	{#if minutesError}<p class="bad" role="alert">{minutesError}</p>{/if}

	<section class="finish" aria-label="Finish the art">
		<h2>Put everything into the game</h2>
		<JobPanel {game} tool="ingest_all" label="Ingest all" ondone={load} />

		<h2>Contact sheet</h2>
		<p class="muted">Shows every symbol at 128 px on the background, landscape and portrait, plus every image with its id.</p>
		<JobPanel {game} tool="contact_sheet" label="Contact sheet" ondone={() => ((contactVersion = Date.now()), load())} />
		{#if contactVersion}
			<div class="contact">
				{#each ['land', 'port', 'all'] as n}
					<a href={`/api/game/${encodeURIComponent(game)}/assets/contact/${n}?v=${contactVersion}`} target="_blank" rel="noopener">
						<img src={`/api/game/${encodeURIComponent(game)}/assets/contact/${n}?v=${contactVersion}`} alt={`contact sheet ${n}`} />
					</a>
				{/each}
			</div>
		{/if}

		<h2>Art-direction checklist</h2>
		<p class="muted">Look at the contact sheet and answer each one before you sign.</p>
		<ol class="checklist">{#each desk.checklist as item}<li>{item}</li>{/each}</ol>

		<h2>Sign off</h2>
		<p class="muted">Signing records your name with a fingerprint of the current files. It only works when every required slot is complete.</p>
		<label class="lbl">Your name <input bind:value={signer} placeholder="First Last" maxlength="60" /></label>
		<JobPanel
			{game}
			tool="sign_off"
			opts={{ signer: signer.trim() }}
			label="Sign off"
			confirm={`Sign off the art as "${signer.trim()}"? You confirm you checked every item on the checklist.`}
			disabled={signer.trim().length < 2 || desk.required.filled < desk.required.total}
			disabledNote={signer.trim().length < 2 ? 'Type your name first.' : 'Every required slot must be complete first.'}
			ondone={load}
		/>
	</section>
{/if}

<style>
	.summary { position: sticky; top: 49px; z-index: 4; display: flex; gap: 22px; align-items: center; flex-wrap: wrap; }
	.summary progress { width: 120px; vertical-align: middle; }
	.sitting { margin-top: 18px; }
	.sithead { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
	.sithead h2 { margin: 0; }
	.mins input { width: 70px; margin-left: 4px; }
	.note { margin: 4px 0 10px; }
	.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 12px; }
	.finish { margin-top: 28px; display: flex; flex-direction: column; gap: 8px; max-width: 900px; }
	.contact { display: flex; gap: 10px; flex-wrap: wrap; }
	.contact img { max-width: 280px; max-height: 280px; border: 1px solid var(--line); border-radius: 4px; }
	.checklist { margin: 0 0 0 18px; padding: 0; }
	.lbl { display: flex; flex-direction: column; gap: 3px; max-width: 320px; color: var(--muted); font-size: 12px; }
</style>
