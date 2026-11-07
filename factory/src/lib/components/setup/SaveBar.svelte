<script lang="ts">
	// Save button + status line shared by the Advanced forms.
	let { dirty, busy, error, ok, onsave, disabled = false }: { dirty: boolean; busy: boolean; error: string; ok: string; onsave: () => void; disabled?: boolean } = $props();
</script>

<div class="savebar">
	<button onclick={onsave} disabled={disabled || busy || !dirty}>{busy ? 'Saving…' : 'Save'}</button>
	{#if dirty}<span class="warn">Unsaved changes</span>{:else if ok}<span class="ok">{ok}</span>{/if}
	{#if error}<span class="bad" role="alert">Could not save: {error}</span>{/if}
</div>

<style>
	.savebar { display: flex; gap: 10px; align-items: center; margin-top: 10px; flex-wrap: wrap; }
</style>
