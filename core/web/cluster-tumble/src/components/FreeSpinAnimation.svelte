<script lang="ts">
	// Bonus card over the board (no Spine): the skin slot card.<variant>.intro flips in (fx 'cardIn').
	// Children are drawn on the card, centred at (0, 0), with the card sizes.
	import type { Snippet } from 'svelte';
	import { Container, Graphics, type Sizes } from 'pixi-svelte';
	import { MainContainer } from 'components-layout';
	import skin from '$skin/skin.generated';

	import AMotion from './fx/AMotion.svelte';
	import SlotVisual from '../slots/SlotVisual.svelte';
	import { palette } from '../slots/slots';
	import { getContext } from '../game/context';
	import { BOARD_SIZES } from '../game/constants';

	type Props = {
		children: Snippet<[{ sizes: Sizes }]>;
	};

	const props: Props = $props();
	const context = getContext();

	// Cards are 3:4 (core/assets/slots.v1.json), about as tall as the board.
	const CARD_SIZES = { width: BOARD_SIZES.height * 1.05 * 0.75, height: BOARD_SIZES.height * 1.05 };
	const variant = $derived(
		context.stateGame.bonusVariant ?? (skin.bonusVariants as readonly string[])[0] ?? 'base',
	);
</script>

<MainContainer>
	<Container
		x={context.stateGameDerived.boardLayout().x}
		y={context.stateGameDerived.boardLayout().y}
	>
		<AMotion preset="cardIn" size={CARD_SIZES.height}>
			{#snippet children()}
				<SlotVisual id={`card.${variant}.intro`} width={CARD_SIZES.width} height={CARD_SIZES.height} />
				<!-- dark plate keeps the texts readable on any card art -->
				<Graphics
					draw={(g) =>
						g
							.roundRect(
								-CARD_SIZES.width * 0.42,
								-CARD_SIZES.height * 0.4,
								CARD_SIZES.width * 0.84,
								CARD_SIZES.height * 0.78,
								CARD_SIZES.width * 0.06,
							)
							.fill({ color: palette[0] ?? '#000000', alpha: 0.55 })}
				/>
				{@render props.children({ sizes: CARD_SIZES })}
			{/snippet}
		</AMotion>
	</Container>
</MainContainer>
