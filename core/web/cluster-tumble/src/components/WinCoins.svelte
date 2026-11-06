<script lang="ts">
	// Coin fountain over the board: code-drawn coins in the palette accent (fx/ACoinBurst), denser per win level.
	import { Container } from 'pixi-svelte';
	import { MainContainer } from 'components-layout';

	import ACoinBurst from './fx/ACoinBurst.svelte';
	import { getContext } from '../game/context';
	import { BOARD_SIZES } from '../game/constants';
	import type { WinLevelAlias } from '../game/winLevelMap';

	type Props = {
		emit?: boolean;
		levelAlias?: WinLevelAlias;
	};

	// Coins per second by win level.
	const RATE: Record<WinLevelAlias, number> = {
		zero: 0,
		standard: 6,
		small: 10,
		nice: 16,
		substantial: 22,
		big: 30,
		superwin: 40,
		mega: 50,
		epic: 60,
		max: 80,
	};

	const props: Props = $props();
	const context = getContext();
	const rate = $derived(props.levelAlias ? RATE[props.levelAlias] : RATE.standard);
</script>

<MainContainer>
	<Container
		x={context.stateGameDerived.boardLayout().x}
		y={context.stateGameDerived.boardLayout().y}
	>
		<ACoinBurst emit={props.emit} {rate} size={BOARD_SIZES.width} />
	</Container>
</MainContainer>
