<script lang="ts" module>
	export type EmitterEventBoardFrame =
		| { type: 'boardFrameGlowShow' }
		| { type: 'boardFrameGlowHide' };
</script>

<script lang="ts">
	// Board frame from the skin (slot frame.board) plus a breathing glow while the game highlights the
	// board (boardFrameGlowShow / Hide). Plan v3.3 slice 10.6b.
	import { Graphics } from 'pixi-svelte';

	import SlotVisual from '../slots/SlotVisual.svelte';
	import { palette } from '../slots/slots';
	import Motion from '../motion/Motion.svelte';
	import { getContext } from '../game/context';

	const context = getContext();
	const FRAME_SCALE = 1.14; // frame art is square with a margin around the board
	const layout = $derived(context.stateGameDerived.boardLayout());
	const side = $derived(Math.max(layout.width, layout.height) * FRAME_SCALE);
	const accent = $derived(parseInt((palette[2] ?? '#ffffff').slice(1, 7), 16));

	let glowing = $state(false);

	context.eventEmitter.subscribeOnMount({
		boardFrameGlowShow: () => (glowing = true),
		boardFrameGlowHide: () => (glowing = false),
	});
</script>

{#if glowing}
	<Motion preset="glowWin" x={layout.x} y={layout.y} zIndex={-1}>
		{#snippet children({ glow })}
			<Graphics
				draw={(g) =>
					g
						.roundRect(-side / 2, -side / 2, side, side, side * 0.04)
						.stroke({ color: accent, width: side * 0.02, alpha: 0.25 + 0.6 * glow })}
			/>
		{/snippet}
	</Motion>
{/if}

<!-- Board backdrop: keeps symbols readable on any background art. -->
<Graphics
	x={layout.x}
	y={layout.y}
	draw={(g) =>
		g
			.roundRect(-layout.width / 2 - 6, -layout.height / 2 - 6, layout.width + 12, layout.height + 12, 14)
			.fill({ color: parseInt((palette[0] ?? '#101018').slice(1, 7), 16), alpha: 0.72 })}
/>

<SlotVisual id="frame.board" x={layout.x} y={layout.y} width={side} height={side} />
