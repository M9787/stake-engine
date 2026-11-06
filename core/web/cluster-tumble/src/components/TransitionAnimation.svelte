<script lang="ts">
	// Screen wipe (no Spine): the skin slot transition.wipe over a palette base slides in from the right,
	// covers the screen, slides out to the left (fx 'wipe'), then calls oncomplete.
	import { Graphics } from 'pixi-svelte';

	import AMotion from './fx/AMotion.svelte';
	import SlotVisual from '../slots/SlotVisual.svelte';
	import { palette } from '../slots/slots';
	import { getContext } from '../game/context';

	type Props = {
		oncomplete: () => void;
	};

	const props: Props = $props();
	const context = getContext();

	const canvas = $derived(context.stateLayoutDerived.canvasSizes());
	// Cover the canvas with margin; the 16:9 wipe art is scaled to cover, never squashed.
	const cover = $derived({ width: canvas.width * 1.2, height: canvas.height * 1.2 });
	const art = $derived.by(() => {
		const s = Math.max(cover.width / 16, cover.height / 9);
		return { width: 16 * s, height: 9 * s };
	});
</script>

<AMotion
	preset="wipe"
	size={cover.width}
	x={canvas.width * 0.5}
	y={canvas.height * 0.5}
	oncomplete={() => props.oncomplete()}
>
	{#snippet children()}
		<Graphics
			draw={(g) =>
				g
					.rect(-cover.width * 0.5, -cover.height * 0.5, cover.width, cover.height)
					.fill({ color: palette[0] ?? '#000000' })}
		/>
		<SlotVisual id="transition.wipe" width={art.width} height={art.height} />
	{/snippet}
</AMotion>
