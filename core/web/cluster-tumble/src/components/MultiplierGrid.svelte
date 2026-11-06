<script lang="ts" module>
	export type EmitterEventMultiplierGrid =
		| { type: 'multiplierGridShow' }
		| { type: 'multiplierGridHide' }
		| { type: 'multiplierGridUpdate'; grid: number[][] }
		| { type: 'multiplierGridClear' };
</script>

<script lang="ts">
	// Multiplier spots: one tinted sigil per marked cell (fx/BSigil). A spot lands when its value
	// changes; at the skin's grid cap it pulses (white-gold).
	import { BitmapText, Container } from 'pixi-svelte';
	import skin from '$skin/skin.generated';

	import BoardContainer from './BoardContainer.svelte';
	import { getContext } from '../game/context';
	import { SYMBOL_SIZE } from '../game/constants';
	import Motion from '../motion/Motion.svelte';
	import { FONT } from '../slots/fonts';
	import BSigil from './fx/BSigil.svelte';

	const context = getContext();
	const GRID_CAP: number = skin.gridCap;
	const SPOT_SIZE = SYMBOL_SIZE * 0.9;
	const DEFAULT_GRID = [
		[0, 0, 0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0, 0, 0],
	];

	let show = $state(false);
	let grid = $state(DEFAULT_GRID);

	context.eventEmitter.subscribeOnMount({
		multiplierGridShow: () => (show = true),
		multiplierGridHide: () => (show = false),
		multiplierGridUpdate: (emitterEvent) => (grid = emitterEvent.grid),
		multiplierGridClear: () => (grid = DEFAULT_GRID),
	});
</script>

<BoardContainer>
	{#if show}
		{#each grid as reel, reelIndex}
			{#each reel as multiplier, rowIndex}
				{#if multiplier > 0}
					{@const atCap = multiplier >= GRID_CAP}
					<Container x={(reelIndex + 0.5) * SYMBOL_SIZE} y={(rowIndex + 0.5) * SYMBOL_SIZE}>
						<Motion preset={atCap ? 'pulse' : 'land'} loop={atCap} play={multiplier} size={SPOT_SIZE}>
							{#snippet children({ glow })}
								<BSigil value={multiplier} cap={GRID_CAP} size={SPOT_SIZE} {glow} />
								{#if multiplier > 1}
									<BitmapText
										anchor={0.5}
										text={`${multiplier}×`}
										style={{
											fontFamily: FONT.accent,
											fontSize: SYMBOL_SIZE * (multiplier >= 100 ? 0.3 : 0.38),
										}}
									/>
								{/if}
							{/snippet}
						</Motion>
					</Container>
				{/if}
			{/each}
		{/each}
	{/if}
</BoardContainer>
