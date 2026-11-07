<script lang="ts">
	// One upload lane of a slot card: drop a file or click to pick one. Posts to the upload endpoint.
	import { errorText } from '$lib/components/JobPanel.svelte';

	type Props = {
		game: string;
		slot: string;
		lane: 'raw' | 'edited';
		title: string;
		accept: string;
		have: string | null;
		disabled?: boolean;
		onuploaded: (card: unknown) => void;
	};
	let { game, slot, lane, title, accept, have, disabled = false, onuploaded }: Props = $props();

	let over = $state(false);
	let busy = $state(false);
	let error = $state('');
	let input = $state<HTMLInputElement | null>(null);

	async function send(file: File | undefined) {
		if (!file || disabled) return;
		if (file.size > 60 * 1024 * 1024) {
			error = 'This file is larger than 60 MB.';
			return;
		}
		busy = true;
		error = '';
		const form = new FormData();
		form.set('slot', slot);
		form.set('lane', lane);
		form.set('file', file);
		try {
			const res = await fetch(`/api/game/${encodeURIComponent(game)}/assets/upload`, { method: 'POST', body: form });
			if (!res.ok) throw new Error(await errorText(res));
			onuploaded(await res.json());
		} catch (e) {
			error = (e as Error).message;
		} finally {
			busy = false;
			if (input) input.value = '';
		}
	}

	function drop(e: DragEvent) {
		e.preventDefault();
		over = false;
		send(e.dataTransfer?.files?.[0]);
	}
</script>

<div
	class="zone"
	class:over
	class:disabled
	role="button"
	tabindex={disabled ? -1 : 0}
	aria-label={`${title} for ${slot}: drop a file or press to choose one`}
	aria-disabled={disabled}
	ondragover={(e) => {
		e.preventDefault();
		if (!disabled) over = true;
	}}
	ondragleave={() => (over = false)}
	ondrop={drop}
	onclick={() => !disabled && input?.click()}
	onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && !disabled && (e.preventDefault(), input?.click())}
>
	<strong>{title}</strong>
	<span class="small">
		{#if busy}Uploading…{:else if have}<span class="ok">{have}</span> · drop to replace{:else}Drop the file here or click{/if}
	</span>
	<input bind:this={input} type="file" {accept} hidden onchange={(e) => send((e.currentTarget as HTMLInputElement).files?.[0])} />
</div>
{#if error}<div class="bad small" role="alert">{error}</div>{/if}

<style>
	.zone { border: 2px dashed var(--line); border-radius: 8px; padding: 10px; display: flex; flex-direction: column; gap: 3px; cursor: pointer; min-height: 48px; }
	.zone.over { border-color: var(--accent); background: #2a2440; }
	.zone.disabled { cursor: not-allowed; opacity: 0.5; }
	.zone:focus-visible { outline: 2px solid var(--accent); }
	.small { font-size: 12px; }
</style>
