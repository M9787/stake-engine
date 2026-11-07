<script lang="ts">
	// One asset slot on the desk: what to make, where, the prompt, the edit recipe, the files and the
	// provenance line. Ingest runs tools/assets/ingest.py --slot through the jobs API (JobPanel).
	import { untrack } from 'svelte';
	import JobPanel, { api, sendJson } from '$lib/components/JobPanel.svelte';
	import DropZone from './DropZone.svelte';
	import type { DeskCard } from './desk';

	type Props = {
		game: string;
		card: DeskCard;
		licences: string[];
		locked: boolean; // greyed: needs the hero style reference first
		version: number; // bumps after a change, so thumbnails reload
		onchange: (card: DeskCard) => void;
		oningested: () => void;
	};
	let { game, card, licences, locked, version, onchange, oningested }: Props = $props();

	const ACCEPT: Record<DeskCard['kind'], string> = {
		image: '.png,.jpg,.jpeg,.webp',
		music: '.wav,.mp3,.ogg,.flac,.m4a',
		sfx: '.wav,.mp3,.ogg,.flac,.m4a',
		font: '.ttf,.otf',
	};

	type Prov = { licence: string; sourceUrl: string; editNote: string; redo: string };
	const fromCard = (c: DeskCard): Prov => ({
		licence: c.provenance.licence ?? '',
		sourceUrl: c.provenance.sourceUrl ?? '',
		editNote: c.provenance.editNote ?? '',
		redo: c.provenance.redo ?? '',
	});
	let prov = $state<Prov>(fromCard(card));
	let saved = $state<Prov>(fromCard(card));
	let saving = $state(false);
	let saveError = $state('');
	let copied = $state(false);
	let showIngest = $state(false);

	// Take server values when the card is refreshed, unless the owner has unsaved typing here.
	$effect(() => {
		const next = fromCard(card);
		untrack(() => {
			const dirty = (Object.keys(prov) as (keyof Prov)[]).some((k) => prov[k] !== saved[k]);
			if (!dirty) prov = next;
			saved = next;
		});
	});

	const showEdited = $derived(card.kind === 'image' || card.humanEdit === 'required');
	const isLink = (u: string) => /^https?:\/\//i.test(u);
	const fileUrl = (lane: string) =>
		`/api/game/${encodeURIComponent(game)}/assets/file?slot=${encodeURIComponent(card.id)}&lane=${lane}&v=${version}`;
	const size = $derived(card.px ? `${card.px[0]}×${card.px[1]} px` : '');
	const reqLabel = $derived(card.required === 'ship' ? 'required' : card.required === 'source' ? 'style source' : 'optional');

	async function copy() {
		try {
			await navigator.clipboard.writeText(card.prompt);
			copied = true;
			setTimeout(() => (copied = false), 1400);
		} catch {
			saveError = 'Copy did not work: select the prompt text and press Ctrl+C.';
		}
	}

	async function save() {
		const changed = (Object.keys(prov) as (keyof Prov)[]).some((k) => prov[k] !== saved[k]);
		if (!changed) return;
		saving = true;
		saveError = '';
		try {
			const c = await api<DeskCard>(`/api/game/${encodeURIComponent(game)}/assets/provenance`, sendJson('PUT', { slot: card.id, ...prov }));
			saved = { ...prov };
			onchange(c);
		} catch (e) {
			saveError = (e as Error).message;
		} finally {
			saving = false;
		}
	}
</script>

<article class="card panel" class:complete={card.complete} class:locked aria-label={`slot ${card.id}`}>
	<div class="head">
		<span class="id">{card.id}</span>
		<span class="badge {card.required}">{reqLabel}</span>
		{#if card.complete}<span class="badge done">complete</span>{/if}
		{#if card.ingested}<span class="badge in">in the game</span>{/if}
		{#if card.drift}<span class="badge drift" title="The style bible changed after this file was made">prompt changed since upload</span>{/if}
	</div>
	<div class="meta muted">
		{card.kind}{#if size} · {size}{/if}{#if card.aspect} · aspect {card.aspect}{/if}{#if card.variants} · make {card.variants}, pick 1{/if}
	</div>
	{#if card.feeds.length}<div class="meta muted">used for: {card.feeds.join(', ')}</div>{/if}
	{#if card.source}<div class="meta muted">look for: {card.source}</div>{/if}

	{#if locked}
		<p class="lockmsg warn">Waiting for the hero: pick the hero image first and put its link in the style reference. This slot unlocks then.</p>
	{/if}

	<div class="tool">
		<strong>{card.toolLabel}</strong>
		{#if card.toolUrl}<a href={card.toolUrl} target="_blank" rel="noopener noreferrer">open</a>{/if}
	</div>
	{#if card.steps.length}
		<ol class="steps">{#each card.steps as st}<li>{st}</li>{/each}</ol>
	{/if}

	<label class="lbl" for={`p-${card.id}`}>Prompt</label>
	<textarea id={`p-${card.id}`} readonly rows="4" value={card.prompt}></textarea>
	<div class="row">
		<button onclick={copy} disabled={locked}>{copied ? 'Copied' : 'Copy prompt'}</button>
		<span class="muted small">prompt id {card.promptSha}</span>
	</div>

	{#if card.editRecipe.length}
		<div class="lbl">Your edit in Photopea (required: a real human change)</div>
		<ol class="steps">{#each card.editRecipe as st}<li>{st}</li>{/each}</ol>
	{/if}

	<div class="thumbs">
		{#each [['raw', card.have.raw], ['edited', card.have.edited], ['final', card.ingested ? 'final' : null]] as [lane, have]}
			{#if have && (lane !== 'edited' || showEdited)}
				<figure>
					{#if card.kind === 'image'}
						<img src={fileUrl(lane as string)} alt={`${card.id} ${lane}`} loading="lazy" />
					{:else if card.kind === 'font'}
						<div class="fontbox muted">{have}</div>
					{:else}
						<audio controls preload="none" src={fileUrl(lane as string)}></audio>
					{/if}
					<figcaption class="muted">{lane === 'raw' ? 'download' : lane === 'edited' ? 'your edit' : 'in the game'}</figcaption>
				</figure>
			{/if}
		{/each}
	</div>

	<div class="zones">
		<DropZone {game} slot={card.id} lane="raw" title="1. The download (raw)" accept={ACCEPT[card.kind]} have={card.have.raw} disabled={locked} onuploaded={(c) => onchange(c as DeskCard)} />
		{#if showEdited}
			<DropZone {game} slot={card.id} lane="edited" title="2. Your edited file" accept={ACCEPT[card.kind]} have={card.have.edited} disabled={locked} onuploaded={(c) => onchange(c as DeskCard)} />
		{/if}
	</div>

	<fieldset class="prov">
		<legend>Where it came from</legend>
		<label class="lbl">Licence
			<select bind:value={prov.licence} onblur={save} onchange={save}>
				<option value="">choose…{card.licenceDefault ? ` (usually ${card.licenceDefault})` : ''}</option>
				{#each licences as l}<option value={l}>{l}</option>{/each}
			</select>
		</label>
		<label class="lbl">Source link (Midjourney job, Suno song or sound page)
			<input type="url" bind:value={prov.sourceUrl} onblur={save} placeholder="https://…" />
		</label>
		{#if prov.sourceUrl && isLink(prov.sourceUrl)}<a class="small" href={prov.sourceUrl} target="_blank" rel="noopener noreferrer">open source link</a>{/if}
		<label class="lbl">What you changed
			<input bind:value={prov.editNote} onblur={save} placeholder="e.g. repainted the runes, recoloured to the palette" />
		</label>
		<label class="lbl">Redo? (leave empty if it is fine)
			<input bind:value={prov.redo} onblur={save} placeholder="what is wrong" />
		</label>
		<span class="small muted">{saving ? 'Saving…' : 'Saved when you leave a field.'}</span>
		{#if saveError}<div class="bad small" role="alert">{saveError}</div>{/if}
	</fieldset>

	{#if card.issues.length && !(card.issues.length === 1 && card.issues[0] === 'no file yet')}
		<ul class="issues">{#each card.issues as i}<li class="warn">{i}</li>{/each}</ul>
	{:else if !card.have.raw}
		<p class="muted small">No file yet.</p>
	{/if}

	{#if card.have.raw && card.required !== 'source'}
		{#if showIngest}
			<JobPanel {game} tool="ingest_slot" opts={{ slot: card.id }} label="Ingest this slot" ondone={() => oningested()} />
		{:else}
			<button class="secondary" onclick={() => (showIngest = true)}>Put this slot into the game…</button>
		{/if}
	{/if}
</article>

<style>
	.card { display: flex; flex-direction: column; gap: 6px; }
	.card.complete { border-color: var(--ok); }
	.card.locked { opacity: 0.55; }
	.head { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
	.id { font-weight: 800; font-size: 15px; }
	.badge { font-size: 11px; padding: 1px 7px; border-radius: 9px; border: 1px solid var(--line); }
	.badge.ship { color: var(--warn); border-color: var(--warn); }
	.badge.optional, .badge.source { color: var(--muted); }
	.badge.done { color: var(--ok); border-color: var(--ok); }
	.badge.in { color: #8fc7ff; border-color: #8fc7ff; }
	.badge.drift { color: var(--bad); border-color: var(--bad); }
	.meta { font-size: 12px; }
	.tool { display: flex; gap: 8px; align-items: baseline; margin-top: 4px; }
	.steps { margin: 2px 0 2px 18px; padding: 0; font-size: 13px; }
	.lbl { font-size: 12px; color: var(--muted); display: flex; flex-direction: column; gap: 2px; margin-top: 4px; }
	textarea { width: 100%; font: 12px/1.4 ui-monospace, monospace; resize: vertical; }
	.row { display: flex; gap: 10px; align-items: center; }
	.small { font-size: 12px; }
	.thumbs { display: flex; gap: 8px; flex-wrap: wrap; }
	figure { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 2px; }
	figure img { width: 96px; height: 96px; object-fit: contain; background: repeating-conic-gradient(#2a2638 0 25%, #1d1a2b 0 50%) 0 0 / 16px 16px; border: 1px solid var(--line); border-radius: 4px; }
	figure audio { width: 220px; }
	.fontbox { padding: 6px; border: 1px solid var(--line); border-radius: 4px; font-size: 12px; }
	figcaption { font-size: 11px; }
	.zones { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
	.prov { border: 1px solid var(--line); border-radius: 6px; padding: 6px 8px; display: flex; flex-direction: column; gap: 2px; }
	.prov legend { font-size: 12px; color: var(--muted); }
	.prov input, .prov select { width: 100%; }
	.issues { margin: 0; padding-left: 18px; font-size: 13px; }
	.lockmsg { margin: 0; font-size: 13px; }
</style>
