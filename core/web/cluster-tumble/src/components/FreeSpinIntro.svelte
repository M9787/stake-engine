<script lang="ts" module>
	export type EmitterEventFreeSpinIntro =
		| { type: 'freeSpinIntroShow' }
		| { type: 'freeSpinIntroHide' }
		| { type: 'freeSpinIntroUpdate'; totalFreeSpins: number };
</script>

<script lang="ts">
	import { CanvasSizeRectangle } from 'components-layout';
	import { FadeContainer } from 'components-pixi';
	import { waitForResolve } from 'utils-shared/wait';
	import { BitmapText, Text } from 'pixi-svelte';
	import skin from '$skin/skin.generated';

	import { getContext } from '../game/context';
	import { t } from '../game/wording';
	import Motion from '../motion/Motion.svelte';
	import { FONT } from '../slots/fonts';
	import { labelStyle } from './fx/AText';
	import PressToContinue from './PressToContinue.svelte';
	import FreeSpinAnimation from './FreeSpinAnimation.svelte';

	const context = getContext();
	const texts = skin.rules.texts as Record<string, string>;

	let show = $state(false);
	let freeSpinsFromEvent = $state(0);
	let oncomplete = $state(() => {});

	// Headline: the bonus title of the variant (text key mode.<variant>.title), else a neutral label.
	const headline = $derived.by(() => {
		const key = `mode.${context.stateGame.bonusVariant}.title`;
		return t(texts[key] ?? 'FREE SPINS');
	});

	context.eventEmitter.subscribeOnMount({
		freeSpinIntroShow: () => (show = true),
		freeSpinIntroHide: () => (show = false),
		freeSpinIntroUpdate: async (emitterEvent) => {
			freeSpinsFromEvent = emitterEvent.totalFreeSpins;
			await waitForResolve((resolve) => (oncomplete = resolve));
		},
	});
</script>

<FadeContainer {show}>
	<CanvasSizeRectangle backgroundColor={0x000000} backgroundAlpha={0.5} />

	<FreeSpinAnimation>
		{#snippet children({ sizes })}
			<Text anchor={0.5} y={-sizes.height * 0.27} text={headline} style={labelStyle(sizes.height * 0.07)} />

			<Motion preset="shockwave" play={freeSpinsFromEvent}>
				{#snippet children()}
					<BitmapText
						anchor={0.5}
						text={String(freeSpinsFromEvent)}
						style={{ fontFamily: FONT.counter, fontSize: sizes.height * 0.26 }}
					/>
				{/snippet}
			</Motion>

			<Text
				anchor={0.5}
				y={sizes.height * 0.22}
				text={t('FREE SPINS')}
				style={labelStyle(sizes.height * 0.06, '#ffffff')}
			/>
		{/snippet}
	</FreeSpinAnimation>

	<PressToContinue onpress={() => oncomplete()} />
</FadeContainer>
