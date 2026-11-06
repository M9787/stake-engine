<script lang="ts" module>
	export type EmitterEventGlobalMultiplier =
		| { type: 'globalMultiplierShow' }
		| { type: 'globalMultiplierHide' }
		| { type: 'globalMultiplierUpdate'; multiplier: number };
</script>

<script lang="ts">
	// Global multiplier badge: sigil + FONT.accent number. The sample Spine animations map to motion
	// presets: static -> 'static', win -> 'pulse', reset -> 'land', increment -> 'shockwave'. The update
	// handler waits for the motion to finish, as it waited for the Spine track before.
	import { Tween } from 'svelte/motion';

	import { BitmapText, Container } from 'pixi-svelte';
	import { FadeContainer } from 'components-pixi';
	import { waitForResolve, waitForTimeout } from 'utils-shared/wait';
	import skin from '$skin/skin.generated';

	import BoardContainer from './BoardContainer.svelte';
	import { getContext } from '../game/context';
	import { SYMBOL_SIZE } from '../game/constants';
	import Motion from '../motion/Motion.svelte';
	import { FONT } from '../slots/fonts';
	import BSigil from './fx/BSigil.svelte';

	type AnimationName = 'static' | 'win' | 'reset' | 'increment';

	const PRESET: Record<AnimationName, string> = {
		static: 'static',
		win: 'pulse',
		reset: 'land',
		increment: 'shockwave',
	};

	const PANEL_WIDTH = SYMBOL_SIZE * 0.641;
	const GRID_CAP: number = skin.gridCap;
	const context = getContext();
	const scale = $derived(context.stateLayoutDerived.isStacked() ? 1.28 : 1);
	const desktopPosition = $derived({
		x: context.stateGameDerived.boardLayout().width - PANEL_WIDTH * 1.3,
		y: -SYMBOL_SIZE * 0.47,
	});
	const portraitPosition = $derived({
		x: context.stateGameDerived.boardLayout().width - PANEL_WIDTH * 1.5,
		y: -SYMBOL_SIZE * 0.55,
	});
	const position = $derived(
		context.stateLayoutDerived.isStacked() ? portraitPosition : desktopPosition,
	);

	let show = $state(false);
	let animationName = $state<AnimationName>('static');
	let multiplier = $state(1);
	let previousMultiplier = new Tween(1);
	let oncomplete = $state(() => {});
	let play = $state(0); // bumped on every update so the motion restarts

	context.eventEmitter.subscribeOnMount({
		globalMultiplierShow: () => (show = true),
		globalMultiplierHide: () => (show = false),
		globalMultiplierUpdate: async (emitterEvent) => {
			if (emitterEvent.multiplier === 1 && multiplier !== 1) {
				animationName = 'reset';
				await waitForTimeout(300);
				context.eventEmitter.broadcast({ type: 'soundOnce', name: 'sfx_multiplier_reset' });
				previousMultiplier.set(emitterEvent.multiplier);
			}

			if (emitterEvent.multiplier > multiplier) {
				context.eventEmitter.broadcast({ type: 'soundOnce', name: 'sfx_multiplier_update' });
				animationName = 'increment';
			}

			if (animationName !== 'static') {
				multiplier = emitterEvent.multiplier;
				const done = waitForResolve((resolve) => (oncomplete = resolve));
				play++;
				await done;
				animationName = 'static';
				previousMultiplier.set(multiplier, { duration: 0 });
			}
		},
	});
</script>

<FadeContainer {show}>
	<BoardContainer>
		<Container {...position} {scale}>
			<Motion
				preset={PRESET[animationName]}
				{play}
				size={PANEL_WIDTH}
				oncomplete={() => {
					if (animationName !== 'static') oncomplete();
				}}
			>
				{#snippet children({ glow })}
					<BSigil value={multiplier} cap={GRID_CAP} size={PANEL_WIDTH} {glow} />
					<BitmapText
						anchor={0.5}
						text={`${animationName === 'static' ? Math.round(previousMultiplier.current) : multiplier}×`}
						style={{
							fontFamily: FONT.accent,
							fontSize: PANEL_WIDTH * 0.42,
						}}
					/>
				{/snippet}
			</Motion>
		</Container>
	</BoardContainer>
</FadeContainer>
