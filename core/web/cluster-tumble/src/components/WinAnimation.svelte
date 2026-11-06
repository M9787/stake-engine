<script lang="ts">
	// Big-win banner (no Spine): skin slot panel.bigwin punches in with 'shockwave', then breathes
	// with 'glowWin'. The banner word is the skin text for the win level (textKey; the max-win
	// signature key arrives the same way). The count-up number is rendered by the parent via children.
	import type { Snippet } from 'svelte';
	import { Container, Graphics, Text } from 'pixi-svelte';
	import skin from '$skin/skin.generated';

	import Motion from '../motion/Motion.svelte';
	import SlotVisual from '../slots/SlotVisual.svelte';
	import { palette, slots } from '../slots/slots';
	import { labelStyle } from './fx/AText';
	import { t } from '../game/wording';
	import { BOARD_SIZES } from '../game/constants';

	type Props = {
		/** Skin text key of the banner word (winLevelData.textKey). */
		textKey: string | null;
		/** Number area of the panel; the parent renders the count-up here. */
		children: Snippet<[{ glow: number; width: number; height: number }]>;
	};

	const props: Props = $props();
	const texts = skin.rules.texts as Record<string, string>;

	const px = slots['panel.bigwin']?.px ?? [1400, 800];
	const width = BOARD_SIZES.width * 1.25;
	const height = width * (px[1] / px[0]);
	const banner = $derived(props.textKey && texts[props.textKey] ? t(texts[props.textKey]) : '');

	let phase = $state<'intro' | 'idle'>('intro');
</script>

<Motion
	preset={phase === 'intro' ? 'shockwave' : 'glowWin'}
	play={phase}
	loop={phase === 'idle'}
	size={width}
	oncomplete={() => (phase = 'idle')}
>
	{#snippet children({ glow })}
		<!-- halo behind the panel -->
		<Graphics
			draw={(g) =>
				g.ellipse(0, 0, width * (0.55 + 0.08 * glow), height * (0.6 + 0.08 * glow)).fill({
					color: palette[2] ?? '#ffffff',
					alpha: 0.12 + 0.25 * glow,
				})}
		/>
		<SlotVisual id="panel.bigwin" {width} {height} />
		{#if banner}
			<Text anchor={0.5} y={-height * 0.27} text={banner} style={labelStyle(height * 0.15)} />
		{/if}
		<Container y={height * 0.08}>
			{@render props.children({ glow, width: width * 0.78, height: height * 0.4 })}
		</Container>
	{/snippet}
</Motion>
