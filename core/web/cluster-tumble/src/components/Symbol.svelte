<script lang="ts">
	// One board symbol (plan v3.3 slice 10.6b): the skin's symbol image (slot symbol.<id>) or its
	// procedural fallback, moved by a motion preset per state (getSymbolInfo). `oncomplete` fires when
	// the state's motion ends, which the reel and tumble logic wait for.
	import { Graphics } from 'pixi-svelte';

	import SlotVisual from '../slots/SlotVisual.svelte';
	import { palette } from '../slots/slots';
	import Motion from '../motion/Motion.svelte';
	import type { SymbolState, RawSymbol } from '../game/types';
	import { SYMBOL_SIZE } from '../game/constants';
	import { getSymbolInfo } from '../game/utils';

	type Props = {
		x?: number;
		y?: number;
		state: SymbolState;
		rawSymbol: RawSymbol;
		oncomplete?: () => void;
		loop?: boolean;
	};

	const props: Props = $props();
	const symbolInfo = $derived(getSymbolInfo({ rawSymbol: props.rawSymbol, state: props.state }));
	const size = $derived(SYMBOL_SIZE * symbolInfo.sizeRatio);
	const showWinFrame = $derived(
		['win', 'postWinStatic', 'explosion'].includes(props.state) && symbolInfo.role !== 'scatter',
	);
	const accent = $derived(parseInt((palette[2] ?? '#ffffff').slice(1, 7), 16));
</script>

{#if showWinFrame}
	<Motion preset="glowWin" x={props.x} y={props.y} size={SYMBOL_SIZE}>
		{#snippet children({ glow })}
			<Graphics
				draw={(g) =>
					g
						.roundRect(-SYMBOL_SIZE * 0.48, -SYMBOL_SIZE * 0.48, SYMBOL_SIZE * 0.96, SYMBOL_SIZE * 0.96, SYMBOL_SIZE * 0.12)
						.stroke({ color: accent, width: SYMBOL_SIZE * 0.05, alpha: 0.45 + 0.55 * glow })}
			/>
		{/snippet}
	</Motion>
{/if}

<Motion
	preset={symbolInfo.preset}
	play={props.state}
	loop={props.loop}
	size={SYMBOL_SIZE}
	x={props.x}
	y={props.y}
	oncomplete={props.oncomplete}
>
	{#snippet children({ glow })}
		{#if glow > 0}
			<Graphics
				draw={(g) => g.circle(0, 0, size * 0.52).fill({ color: accent, alpha: 0.35 * glow })}
			/>
		{/if}
		<SlotVisual id={'symbol.' + props.rawSymbol.name} width={size} height={size} />
	{/snippet}
</Motion>
