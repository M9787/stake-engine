<script lang="ts">
	// Loading screen (no Spine, no progress-bar sprites): pulsing logo.emblem, game title from the skin
	// texts, palette progress bar drawn in code, then press-to-continue and the wipe into the game.
	import { Container, Graphics, Text } from 'pixi-svelte';
	import { FadeContainer, LoadingProgress } from 'components-pixi';
	import { MainContainer } from 'components-layout';
	import skin from '$skin/skin.generated';

	import { getContext } from '../game/context';
	import Motion from '../motion/Motion.svelte';
	import SlotVisual from '../slots/SlotVisual.svelte';
	import { isFilled, palette } from '../slots/slots';
	import { labelStyle } from './fx/AText';
	import TransitionAnimation from './TransitionAnimation.svelte';
	import PressToContinue from './PressToContinue.svelte';

	type Props = {
		onloaded: () => void;
	};

	const props: Props = $props();
	const context = getContext();
	const title = (skin.rules.texts as Record<string, string>)['game.name'] ?? skin.displayName.toUpperCase();
	const BAR = { width: 400, height: 24 };

	let loadingType = $state<'start' | 'transition'>('start');
</script>

<!-- logo and loading progress -->
<FadeContainer show={loadingType === 'start'}>
	<MainContainer>
		<Container
			x={context.stateLayoutDerived.mainLayout().width * 0.5}
			y={context.stateLayoutDerived.mainLayout().height * 0.5}
		>
			<!-- slot images are not preloaded: a filled emblem shows once the assets are in -->
			{#if context.stateApp.loaded || !isFilled('logo.emblem')}
				<Motion preset="pulse" loop y={-90}>
					{#snippet children()}
						<SlotVisual id="logo.emblem" width={260} height={260} />
					{/snippet}
				</Motion>
			{/if}
			<Text anchor={0.5} y={90} text={title} style={labelStyle(56)} />
			{#if !context.stateApp.loaded}
				<LoadingProgress y={160} width={BAR.width} height={BAR.height}>
					{#snippet background(sizes)}
						<Graphics
							draw={(g) =>
								g.roundRect(0, 0, sizes.width, sizes.height, sizes.height / 2).fill({ color: palette[0] ?? '#000000' })}
						/>
					{/snippet}
					{#snippet progress(sizes)}
						<Graphics
							draw={(g) =>
								g.roundRect(0, 0, sizes.width, sizes.height, sizes.height / 2).fill({ color: palette[2] ?? '#ffffff' })}
						/>
					{/snippet}
					{#snippet frame(sizes)}
						<Graphics
							draw={(g) =>
								g
									.roundRect(0, 0, sizes.width, sizes.height, sizes.height / 2)
									.stroke({ color: palette[1] ?? '#888888', width: 3 })}
						/>
					{/snippet}
				</LoadingProgress>
			{/if}
		</Container>
	</MainContainer>
</FadeContainer>

<!-- press to continue -->
<FadeContainer show={loadingType === 'start' && context.stateApp.loaded}>
	<PressToContinue onpress={() => (loadingType = 'transition')} />
</FadeContainer>

<!-- transition between the loading screen and the game -->
<FadeContainer show={loadingType === 'transition'}>
	<TransitionAnimation oncomplete={props.onloaded} />
</FadeContainer>
