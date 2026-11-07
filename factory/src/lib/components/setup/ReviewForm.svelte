<script lang="ts">
	// Review + listing: what makes the game original, and the Stake Studio listing texts (game.json review / listing).
	import { saveSection, type SaveResult } from './save';
	import SaveBar from './SaveBar.svelte';

	let { game, review, listing, onsaved }: { game: string; review: any; listing: any; onsaved: (r: SaveResult) => void } = $props();

	const initial = () => ({
		signatureMoment: review?.signatureMoment ?? '',
		originality: [...(review?.originality ?? [])].join('\n'),
		blurb: listing?.blurb ?? '',
		features: [...(listing?.features ?? [])].join('\n'),
		reviewerNotes: listing?.reviewerNotes ?? '',
		distribution: listing?.distribution ?? '',
	});
	let form = $state(initial());
	const start = JSON.stringify(initial());
	let busy = $state(false);
	let error = $state('');
	let ok = $state('');
	const dirty = $derived(JSON.stringify(form) !== start);
	const lines = (t: string) => t.split('\n').map((x) => x.trim()).filter(Boolean);

	async function save() {
		busy = true;
		error = '';
		ok = '';
		try {
			const r = await saveSection(game, 'review', {
				review: { signatureMoment: form.signatureMoment.trim(), originality: lines(form.originality) },
				listing: { blurb: form.blurb.trim(), features: lines(form.features), reviewerNotes: form.reviewerNotes.trim(), distribution: form.distribution },
			});
			ok = 'Saved.';
			onsaved(r);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			busy = false;
		}
	}
</script>

<div class="grid">
	<section>
		<h3>Review</h3>
		<label class="f">
			<span>Signature moment</span>
			<textarea rows="3" bind:value={form.signatureMoment} aria-label="Signature moment"></textarea>
			<em>The one moment players will remember (at least 10 characters).</em>
		</label>
		<label class="f">
			<span>What is new (one per line)</span>
			<textarea rows="4" bind:value={form.originality} aria-label="Originality"></textarea>
			<em>At least two ways the mechanics differ from earlier games.</em>
		</label>
	</section>
	<section>
		<h3>Stake listing</h3>
		<label class="f">
			<span>Short description</span>
			<textarea rows="4" maxlength="600" bind:value={form.blurb} aria-label="Listing description"></textarea>
			<em>Theme and how it plays, up to 600 characters ({form.blurb.length}).</em>
		</label>
		<label class="f">
			<span>Feature bullets (one per line)</span>
			<textarea rows="4" bind:value={form.features} aria-label="Listing features"></textarea>
			<em>Up to 10 lines of 120 characters.</em>
		</label>
		<label class="f">
			<span>Notes for reviewers</span>
			<textarea rows="3" maxlength="2000" bind:value={form.reviewerNotes} aria-label="Reviewer notes"></textarea>
			<em>How to reach the bonus, anything special to look at.</em>
		</label>
		<label class="f">
			<span>Where it is offered</span>
			<select bind:value={form.distribution} aria-label="Distribution">
				<option value="">Not decided yet</option>
				<option value="onlyStake">Stake only</option>
				<option value="network">Stake and the Engine network (no reskins later)</option>
			</select>
			<em>Fixed when the game launches.</em>
		</label>
	</section>
</div>
<SaveBar {dirty} {busy} {error} {ok} onsave={save} />

<style>
	.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; }
	h3 { margin: 0 0 6px; font-size: 15px; }
	.f { display: flex; flex-direction: column; gap: 3px; margin: 8px 0; }
	.f span { font-weight: 600; }
	.f em { color: var(--muted); font-style: normal; font-size: 12px; }
	textarea { width: 100%; resize: vertical; }
</style>
