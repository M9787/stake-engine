<script lang="ts" module>
	export type EmitterEventFreeSpinCounter =
		| { type: 'freeSpinCounterShow' }
		| { type: 'freeSpinCounterHide' }
		| { type: 'freeSpinCounterUpdate'; current?: number; total?: number };
</script>

<script lang="ts">
	// Free spin counter left of the board: palette panel drawn in code, sigil ornament, label in the
	// UI font and the count in the runtime bitmap font FONT.counter.
	import { MainContainer } from 'components-layout';
	import { FadeContainer } from 'components-pixi';
	import { BitmapText, Graphics, Text } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { SYMBOL_SIZE } from '../game/constants';
	import { t } from '../game/wording';
	import { FONT } from '../slots/fonts';
	import { palette } from '../slots/slots';
	import SlotVisual from '../slots/SlotVisual.svelte';
	import { labelStyle } from './fx/AText';

	const context = getContext();
	const PANEL_RATIO = 824 / 622;
	const panelSizes = { width: SYMBOL_SIZE * 2, height: (SYMBOL_SIZE * 2) / PANEL_RATIO };
	const position = $derived({
		x:
			context.stateGameDerived.boardLayout().x -
			context.stateGameDerived.boardLayout().width * 0.5 -
			panelSizes.width -
			SYMBOL_SIZE * 0.7,
		y:
			context.stateGameDerived.boardLayout().y -
			context.stateGameDerived.boardLayout().height * 0.5,
	});

	let show = $state(false);
	let current = $state(0);
	let total = $state(0);

	context.eventEmitter.subscribeOnMount({
		freeSpinCounterShow: () => (show = true),
		freeSpinCounterHide: () => (show = false),
		freeSpinCounterUpdate: (emitterEvent) => {
			if (emitterEvent.current !== undefined) current = emitterEvent.current;
			if (emitterEvent.total !== undefined) total = emitterEvent.total;
		},
	});
</script>

<MainContainer>
	<FadeContainer {show} {...position}>
		<Graphics
			draw={(g) =>
				g
					.roundRect(0, 0, panelSizes.width, panelSizes.height, panelSizes.height * 0.16)
					.fill({ color: palette[0] ?? '#000000', alpha: 0.85 })
					.stroke({ color: palette[2] ?? '#ffffff', width: 3 })}
		/>
		<SlotVisual id="sigil" x={panelSizes.width * 0.5} y={0} width={SYMBOL_SIZE * 0.5} height={SYMBOL_SIZE * 0.5} />
		<Text
			anchor={0.5}
			x={panelSizes.width * 0.5}
			y={panelSizes.height * 0.38}
			text={t('FREE SPINS')}
			style={labelStyle(SYMBOL_SIZE * 0.2)}
		/>
		<BitmapText
			anchor={0.5}
			x={panelSizes.width * 0.5}
			y={panelSizes.height * 0.7}
			text={`${current} / ${total}`}
			style={{ fontFamily: FONT.counter, fontSize: SYMBOL_SIZE * 0.36 }}
		/>
	</FadeContainer>
</MainContainer>
