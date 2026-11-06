<script lang="ts" module>
	import type { WinLevelData } from '../game/winLevelMap';

	export type EmitterEventFreeSpinOutro =
		| { type: 'freeSpinOutroShow' }
		| { type: 'freeSpinOutroHide' }
		| { type: 'freeSpinOutroCountUp'; amount: number; winLevelData: WinLevelData };
</script>

<script lang="ts">
	import { Text } from 'pixi-svelte';
	import { FadeContainer, WinCountUpProvider } from 'components-pixi';
	import { bookEventAmountToCurrencyString } from 'utils-shared/amount';
	import { waitForResolve } from 'utils-shared/wait';
	import { CanvasSizeRectangle } from 'components-layout';
	import { OnMount } from 'components-shared';
	import skin from '$skin/skin.generated';

	import { getContext } from '../game/context';
	import { t } from '../game/wording';
	import Motion from '../motion/Motion.svelte';
	import { labelStyle } from './fx/AText';
	import AWinNumber from './fx/AWinNumber.svelte';
	import FreeSpinAnimation from './FreeSpinAnimation.svelte';
	import PressToContinue from './PressToContinue.svelte';
	import WinCoins from './WinCoins.svelte';

	const context = getContext();
	const texts = skin.rules.texts as Record<string, string>;

	let show = $state(true);
	let amount = $state(0);
	let winLevelData = $state<WinLevelData>();
	let oncomplete = $state(() => {});
	let onCountUpComplete = $state(() => {});

	// Headline: the win-level word for big wins (skin text), else a neutral label.
	const headline = $derived(
		winLevelData?.textKey && texts[winLevelData.textKey] ? t(texts[winLevelData.textKey]) : t('YOU WON'),
	);

	context.eventEmitter.subscribeOnMount({
		freeSpinOutroShow: () => (show = true),
		freeSpinOutroHide: async () => (show = false),
		freeSpinOutroCountUp: async (emitterEvent) => {
			amount = emitterEvent.amount;
			winLevelData = emitterEvent.winLevelData;
			await waitForResolve((resolve) => (oncomplete = resolve));
		},
	});
</script>

<FadeContainer {show}>
	{#if winLevelData}
		{@const duration = winLevelData.presentDuration}
		<WinCountUpProvider {amount} {duration} oncomplete={() => onCountUpComplete()}>
			{#snippet children({ countUpAmount, startCountUp, finishCountUp, countUpCompleted })}
				<OnMount onmount={() => startCountUp()} />

				<CanvasSizeRectangle backgroundColor={0x000000} backgroundAlpha={0.5} />

				<FreeSpinAnimation>
					{#snippet children({ sizes })}
						<Text anchor={0.5} y={-sizes.height * 0.27} text={headline} style={labelStyle(sizes.height * 0.07)} />

						<Motion preset="glowWin" loop>
							{#snippet children({ glow })}
								<AWinNumber
									text={bookEventAmountToCurrencyString(countUpAmount)}
									fontSize={sizes.height * 0.16}
									maxWidth={sizes.width * 0.78}
									{glow}
								/>
							{/snippet}
						</Motion>

						<Text
							anchor={0.5}
							y={sizes.height * 0.22}
							text={t('TOTAL WIN')}
							style={labelStyle(sizes.height * 0.06, '#ffffff')}
						/>
					{/snippet}
				</FreeSpinAnimation>

				<WinCoins emit={!countUpCompleted} levelAlias={winLevelData?.alias} />

				<PressToContinue onpress={() => (countUpCompleted ? oncomplete() : finishCountUp())} />
			{/snippet}
		</WinCountUpProvider>
	{/if}
</FadeContainer>
