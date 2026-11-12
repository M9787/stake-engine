<script lang="ts" module>
	export type Props = {
		/** Slot id from core/assets/slots.v1.json, e.g. 'symbol.H1', 'bg.base.land', 'panel.bigwin'. */
		id: string;
		width: number;
		height: number;
		x?: number;
		y?: number;
		/** 0.5 centres the visual on (x, y); 0 puts its top-left corner there. */
		anchor?: number;
		alpha?: number;
	};
</script>

<script lang="ts">
	// One visual per asset slot (plan v3.3 section 1): the skin's image when the slot is filled, else the
	// slot's procedural fallback. Motion presets (src/motion) wrap this component.
	import { Container, Graphics, Sprite, getContextApp } from 'pixi-svelte';

	import { drawFallback } from './procedural';
	import { isFilled, palette, slotKey, slots } from './slots';

	const props: Props = $props();
	const anchor = $derived(props.anchor ?? 0.5);
	const entry = $derived(slots[props.id]);
	// Draw the image only once its texture is loaded (Stake: no console errors); until then the fallback.
	const app = getContextApp();
	const ready = $derived(isFilled(props.id) && !!app.stateApp.loadedAssets?.[slotKey(props.id)]);
</script>

{#if ready}
	<Sprite
		key={slotKey(props.id)}
		x={props.x ?? 0}
		y={props.y ?? 0}
		width={props.width}
		height={props.height}
		anchor={anchor}
		alpha={props.alpha ?? 1}
	/>
{:else}
	<Container
		x={(props.x ?? 0) - props.width * anchor}
		y={(props.y ?? 0) - props.height * anchor}
		alpha={props.alpha ?? 1}
	>
		<Graphics
			draw={(g) => drawFallback(g, entry?.fallback ?? null, props.width, props.height, palette, props.id, entry?.tier)}
		/>
	</Container>
{/if}
