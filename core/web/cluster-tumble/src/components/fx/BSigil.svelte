<script lang="ts">
	// Multiplier spot: the skin's 'sigil' image tinted per value, or a code-drawn disc when the slot is
	// empty. `glow` (0..1, from a Motion preset) adds a soft halo.
	import { Container, Graphics, Sprite } from 'pixi-svelte';

	import { isFilled, slotKey } from '../../slots/slots';
	import { sigilLook } from './BColor';

	type Props = {
		value: number;
		cap: number;
		size: number;
		glow?: number;
	};

	const props: Props = $props();
	const look = $derived(sigilLook(props.value, props.cap));
	const filled = isFilled('sigil');
	const r = $derived(props.size / 2);
</script>

<Container alpha={look.alpha}>
	<!-- halo and rim, drawn behind the image -->
	<Graphics
		draw={(g) => {
			const glow = props.glow ?? 0;
			if (glow > 0) g.circle(0, 0, r * (1.05 + 0.2 * glow)).fill({ color: look.fill, alpha: 0.25 * glow });
			if (!filled) g.circle(0, 0, r * 0.92).fill({ color: look.fill });
			if (look.rim !== null) g.circle(0, 0, r * 0.95).stroke({ color: look.rim, width: r * 0.12 });
		}}
	/>
	{#if filled}
		<Sprite key={slotKey('sigil')} anchor={0.5} width={props.size * 0.9} height={props.size * 0.9} tint={look.fill} />
	{:else}
		<Graphics draw={(g) => g.circle(-r * 0.25, -r * 0.25, r * 0.2).fill({ color: 0xffffff, alpha: 0.35 })} />
	{/if}
</Container>
