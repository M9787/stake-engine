<!--
	Core copy of components-ui-pixi ButtonBet.svelte (web-sdk packages are read-only).
	Space starts a spin only when the jurisdiction allows the spacebar.
	Low balance (Engine [222]): the button looks disabled, and a press (click or Space) explains
	why instead of doing nothing; no play request is sent. Stop stays usable mid-round.
-->
<script lang="ts">
	import { Container, Text } from 'pixi-svelte';
	import { Button, type ButtonProps } from 'components-pixi';
	import { OnHotkey } from 'components-shared';
	import { stateBet, stateBetDerived, stateConfig, stateModal } from 'state-shared';

	import UiSprite from 'components-ui-pixi/src/components/UiSprite.svelte';
	import ButtonBetProvider from 'components-ui-pixi/src/components/ButtonBetProvider.svelte';
	import { UI_BASE_FONT_SIZE, UI_BASE_SIZE } from 'components-ui-pixi/src/constants';
	import { i18nDerived } from 'components-ui-pixi/src/i18n/i18nDerived';

	import { UI_FONT } from '../../slots/fonts';

	const props: Partial<Omit<ButtonProps, 'children'>> = $props();
	const lowBalance = $derived(!stateBetDerived.isBetCostAvailable());
	const sizes = { width: UI_BASE_SIZE, height: UI_BASE_SIZE };

	// key 'spin_*' = idle (next press bets), 'stop_*' = a round is playing.
	const guard = (key: string, onpress: () => void) => () => {
		if (key.startsWith('spin') && lowBalance) {
			stateModal.modal = { name: 'error', error: { error: 'ERR_IPB', message: 'insufficient balance' } };
			return;
		}
		// jurisdiction.disabledSlamstop: no skipping to the result mid-round. Stopping autoplay
		// (no more rounds after this one) stays allowed.
		if (key.startsWith('stop') && stateConfig.jurisdiction?.disabledSlamstop) {
			if (stateBetDerived.hasAutoBetCounter()) stateBet.autoSpinsCounter = 0;
			return;
		}
		onpress();
	};
</script>

<ButtonBetProvider>
	{#snippet children({ key, onpress })}
		{@const disabled = key === 'stop_disabled'}
		<OnHotkey
			hotkey="Space"
			disabled={disabled || !!stateConfig.jurisdiction?.disabledSpacebar}
			onpress={guard(key, onpress)}
		/>
		<Button {...props} {sizes} onpress={guard(key, onpress)} {disabled}>
			{#snippet children({ center, hovered })}
				<Container {...center}>
					<UiSprite
						key="bet"
						width={sizes.width}
						height={sizes.height}
						anchor={0.5}
						{...['spin_disabled', 'stop_disabled'].includes(key)
							? {
									backgroundColor: 0xaaaaaa,
								}
							: {}}
					/>
					<Text
						anchor={0.5}
						text={['spin_default', 'spin_disabled'].includes(key)
							? i18nDerived.bet()
							: i18nDerived.stop()}
						style={{
							align: 'center',
							wordWrap: true,
							wordWrapWidth: 200,
							fontFamily: UI_FONT,
							fontWeight: '600',
							fontSize: UI_BASE_FONT_SIZE * 0.9,
							fill: 0xffffff,
						}}
					/>
				</Container>
			{/snippet}
		</Button>
	{/snippet}
</ButtonBetProvider>
