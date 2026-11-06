<script lang="ts">
	// Backgrounds from the skin (plan v3.3 slice 10.6b): bg.base.* in the base game, bg.<variant>.* in the
	// bonus of that variant; landscape or portrait art by layout. Image + slow parallax drift, cross-fade.
	import { Rectangle } from 'pixi-svelte';
	import { FadeContainer } from 'components-pixi';
	import { SECOND } from 'constants-shared/time';

	import SlotVisual from '../slots/SlotVisual.svelte';
	import { slots } from '../slots/slots';
	import Motion from '../motion/Motion.svelte';
	import { getContext } from '../game/context';

	const context = getContext();
	const canvas = $derived(context.stateLayoutDerived.canvasSizes());
	const orientation = $derived(context.stateLayoutDerived.layoutType() === 'portrait' ? 'port' : 'land');
	const featureId = $derived(context.stateGame.bonusVariant ?? 'base');
	const showBase = $derived(context.stateGame.gameType === 'basegame');
	const showFeature = $derived(context.stateGame.gameType === 'freegame');

	/** Size that covers the canvas for the slot's aspect ratio (slight overscan for the drift). */
	const cover = (slot: string) => {
		const [w, h] = slots[slot]?.px ?? [canvas.width, canvas.height];
		const k = Math.max(canvas.width / w, canvas.height / h) * 1.03;
		return { width: w * k, height: h * k };
	};
	const baseSlot = $derived(`bg.base.${orientation}`);
	const featureSlot = $derived(slots[`bg.${featureId}.${orientation}`] ? `bg.${featureId}.${orientation}` : baseSlot);
</script>

<Rectangle {...canvas} backgroundColor={0x000000} zIndex={-3} />

<FadeContainer show={showBase} duration={SECOND} zIndex={-2}>
	<Motion preset="parallax" x={canvas.width / 2} y={canvas.height / 2} size={Math.max(canvas.width, canvas.height)}>
		{#snippet children()}
			<SlotVisual id={baseSlot} {...cover(baseSlot)} />
		{/snippet}
	</Motion>
</FadeContainer>

<FadeContainer show={showFeature} duration={SECOND} zIndex={-1}>
	<Motion preset="parallax" x={canvas.width / 2} y={canvas.height / 2} size={Math.max(canvas.width, canvas.height)}>
		{#snippet children()}
			<SlotVisual id={featureSlot} {...cover(featureSlot)} />
		{/snippet}
	</Motion>
</FadeContainer>
