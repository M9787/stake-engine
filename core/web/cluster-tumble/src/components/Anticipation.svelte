<script lang="ts">
	// Column highlight while a reel anticipates (replaces the sample Spine rig): fades in, breathes with
	// the 'glowWin' motion while the reel spins, fades out once it stops, then calls oncomplete.
	import { onMount } from 'svelte';
	import { Tween } from 'svelte/motion';

	import { Container, Graphics } from 'pixi-svelte';
	import { stateBetDerived } from 'state-shared';

	import { getContext } from '../game/context';
	import type { Reel } from '../game/stateGame.svelte';
	import { REEL_PADDING, SYMBOL_SIZE } from '../game/constants';
	import Motion from '../motion/Motion.svelte';
	import { pal } from './fx/BColor';

	type Props = {
		reel: Reel;
		oncomplete: () => void;
	};

	const props: Props = $props();
	const context = getContext();

	const WIDTH = SYMBOL_SIZE * 0.96;
	const height = $derived(context.stateGameDerived.boardLayout().height);
	const alpha = new Tween(0);
	let leaving = false;

	// intro
	onMount(() => {
		alpha.set(1, { duration: 250 / stateBetDerived.timeScale() });
	});

	// out: once the reel has stopped
	$effect(() => {
		if (props.reel.reelState.motion === 'stopped' && !leaving) {
			leaving = true;
			alpha.set(0, { duration: 300 / stateBetDerived.timeScale() }).then(() => props.oncomplete());
		}
	});
</script>

<Container
	x={context.stateGameDerived.boardLayout().x -
		context.stateGameDerived.boardLayout().width * 0.5 +
		(props.reel.reelIndex + REEL_PADDING) * SYMBOL_SIZE}
	y={context.stateGameDerived.boardLayout().y - SYMBOL_SIZE * 0.06}
	alpha={alpha.current}
>
	<Motion preset="glowWin" loop>
		{#snippet children({ glow })}
			<Graphics
				draw={(g) => {
					const w = WIDTH;
					const h = height;
					const r = w * 0.18;
					// soft outer glow: widening strokes with falling alpha
					for (let i = 3; i >= 1; i--) {
						const pad = i * SYMBOL_SIZE * 0.05 * (0.6 + 0.4 * glow);
						g.roundRect(-w / 2 - pad, -h / 2 - pad, w + pad * 2, h + pad * 2, r + pad).stroke({
							color: pal(4),
							width: SYMBOL_SIZE * 0.05,
							alpha: (0.12 + 0.18 * glow) / i,
						});
					}
					g.roundRect(-w / 2, -h / 2, w, h, r)
						.fill({ color: pal(2), alpha: 0.08 + 0.14 * glow })
						.stroke({ color: pal(2), width: SYMBOL_SIZE * 0.04, alpha: 0.6 + 0.4 * glow });
				}}
			/>
		{/snippet}
	</Motion>
</Container>
