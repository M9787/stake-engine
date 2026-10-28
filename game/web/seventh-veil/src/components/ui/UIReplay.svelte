<!--
	Seventh Veil copy of components-ui-pixi UIReplay.svelte (web-sdk packages are read-only).
	Changes vs the shared version (Engine replay guidelines):
	- no EnableSpaceHold and no bet menu: replay offers no route into play [171];
	- shows bet, mode, cost multiplier and real cost = amount x cost [174];
	- REPLAY button restarts the same event once the round is done [173].
-->
<script lang="ts">
	import { Container, Rectangle, Text } from 'pixi-svelte';
	import { Button } from 'components-pixi';
	import { MainContainer } from 'components-layout';
	import { BLACK } from 'constants-shared/colors';
	import { stateBet, stateBetDerived, stateUi } from 'state-shared';
	import { numberToCurrencyString } from 'utils-shared/amount';

	import UiFadeContainer from 'components-ui-pixi/src/components/UiFadeContainer.svelte';
	import UiLabel from 'components-ui-pixi/src/components/UiLabel.svelte';
	import UiSprite from 'components-ui-pixi/src/components/UiSprite.svelte';
	import LabelWin from 'components-ui-pixi/src/components/LabelWin.svelte';
	import ButtonPayTable from 'components-ui-pixi/src/components/ButtonPayTable.svelte';
	import ButtonGameRules from 'components-ui-pixi/src/components/ButtonGameRules.svelte';
	import ButtonSettings from 'components-ui-pixi/src/components/ButtonSettings.svelte';
	import ButtonTurbo from 'components-ui-pixi/src/components/ButtonTurbo.svelte';
	import ButtonMenu from 'components-ui-pixi/src/components/ButtonMenu.svelte';
	import ButtonMenuClose from 'components-ui-pixi/src/components/ButtonMenuClose.svelte';
	import ButtonSoundSwitch from 'components-ui-pixi/src/components/ButtonSoundSwitch.svelte';
	import LabelFreeSpinCounter from 'components-ui-pixi/src/components/LabelFreeSpinCounter.svelte';
	import { UI_BASE_FONT_SIZE, UI_BASE_SIZE } from 'components-ui-pixi/src/constants';
	import type { LayoutUiProps } from 'components-ui-pixi/src/types';

	import { getContext } from '../../game/context';
	import { stateReplay } from '../../game/stateReplay.svelte';
	import { t } from '../../game/wording';

	type Props = {
		gameName: LayoutUiProps['gameName'];
		logo: LayoutUiProps['logo'];
	};

	const props: Props = $props();
	const context = getContext();

	const cost = $derived(stateBetDerived.activeBetMode()?.costMultiplier ?? stateReplay.costMultiplier);
	const modeName = $derived(stateBetDerived.activeBetMode()?.text.title || stateBet.activeBetModeKey);
	const betText = $derived(numberToCurrencyString(stateBet.betAmount));
	const costText = $derived(numberToCurrencyString(stateBet.betAmount * cost));
	const canReplay = $derived(context.stateXstateDerived.isIdle() && !!stateReplay.round);
	const buttonSize = { width: UI_BASE_SIZE, height: UI_BASE_SIZE };

	const replayAgain = () => {
		if (!canReplay || !stateReplay.round) return;
		stateBet.betToResume = { ...stateReplay.round };
		context.eventEmitter.broadcast({ type: 'resumeBet' });
	};
</script>

<UiFadeContainer>
	<Container x={20}>
		{@render props.gameName()}
	</Container>

	<Container x={context.stateLayoutDerived.canvasSizes().width - 20}>
		{@render props.logo()}
	</Container>

	<MainContainer standard alignVertical="bottom">
		{#if stateUi.freeSpinCounterShow && ['portrait', 'tablet'].includes(context.stateLayoutDerived.layoutType())}
			<Container x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5} y={120}>
				<LabelFreeSpinCounter stacked />
			</Container>
		{/if}

		<Container
			x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5}
			y={context.stateLayoutDerived.mainLayoutStandard().height - 270}
			scale={0.8}
		>
			<LabelWin stacked />
		</Container>

		<Container
			x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5}
			y={context.stateLayoutDerived.mainLayoutStandard().height - 150}
			scale={0.8}
		>
			<UiLabel
				tiled
				stacked
				label={cost > 1 ? `${t(modeName)} ×${cost}` : t('BET')}
				value={cost > 1 ? `${betText} · ${t('REAL COST')} ${costText}` : betText}
			/>
		</Container>

		<Container
			x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5 - 350}
			y={context.stateLayoutDerived.mainLayoutStandard().height - 270 - 15}
			scale={0.7}
		>
			<ButtonMenu />
		</Container>

		<Container
			x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5 - 350}
			y={context.stateLayoutDerived.mainLayoutStandard().height - 150 - 15}
			scale={0.7}
		>
			<ButtonTurbo />
		</Container>

		<Container
			x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5 + 350}
			y={context.stateLayoutDerived.mainLayoutStandard().height - 210}
			scale={0.7}
		>
			<Button sizes={buttonSize} onpress={replayAgain} disabled={!canReplay}>
				{#snippet children({ center })}
					<Container {...center}>
						<UiSprite
							key="bet"
							width={buttonSize.width}
							height={buttonSize.height}
							anchor={0.5}
							{...canReplay ? {} : { backgroundColor: 0xaaaaaa }}
						/>
						<Text
							anchor={0.5}
							text={t('REPLAY')}
							style={{
								align: 'center',
								fontFamily: 'proxima-nova',
								fontWeight: '600',
								fontSize: UI_BASE_FONT_SIZE * 0.8,
								fill: 0xffffff,
							}}
						/>
					</Container>
				{/snippet}
			</Button>
		</Container>
	</MainContainer>

	{#if stateUi.menuOpen}
		<Rectangle
			eventMode="static"
			cursor="pointer"
			alpha={0.5}
			anchor={0.5}
			backgroundColor={BLACK}
			width={context.stateLayoutDerived.canvasSizes().width}
			height={context.stateLayoutDerived.canvasSizes().height}
			x={context.stateLayoutDerived.canvasSizes().width * 0.5}
			y={context.stateLayoutDerived.canvasSizes().height * 0.5}
			onpointerup={() => (stateUi.menuOpen = false)}
		/>

		<MainContainer standard alignVertical="bottom">
			<Container
				x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5 - 350}
				y={context.stateLayoutDerived.mainLayoutStandard().height - 270 - 15}
			>
				<Container scale={0.8} y={0 * 0.5 - 150 - 170 * 3}>
					<ButtonPayTable anchor={0.5} />
				</Container>

				<Container scale={0.8} y={0 * 0.5 - 150 - 170 * 2}>
					<ButtonGameRules anchor={0.5} />
				</Container>

				<Container scale={0.8} y={0 * 0.5 - 150 - 170 * 1}>
					<ButtonSettings anchor={0.5} />
				</Container>

				<Container scale={0.8} y={0 * 0.5 - 150}>
					<ButtonSoundSwitch anchor={0.5} />
				</Container>

				<Container scale={0.8} y={0 * 0.5}>
					<ButtonMenuClose anchor={0.5} />
				</Container>
			</Container>
		</MainContainer>
	{/if}
</UiFadeContainer>
