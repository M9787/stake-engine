<script lang="ts">
	import { onMount } from 'svelte';

	import { EnablePixiExtension } from 'components-pixi';
	import { EnableHotkey } from 'components-shared';
	import { MainContainer } from 'components-layout';
	import { App } from 'pixi-svelte';
	import { stateBet, stateConfig, stateModal } from 'state-shared';
	import { stateSession } from '../game/stateSession.svelte';

	import { UiGameName } from 'components-ui-pixi';
	import UI from './ui/UI.svelte';
	import { GameVersion } from 'components-ui-html';
	declare const __GAME_VERSION__: string;
	const gameVersion = __GAME_VERSION__;

	import { getContext } from '../game/context';
	import { initBetModes } from '../game/betModes';
	import GameModals from './GameModals.svelte';
	import EnableJurisdiction from './EnableJurisdiction.svelte';
	import EnableSound from './EnableSound.svelte';
	import EnableGameActor from './EnableGameActor.svelte';
	import ResumeBet from './ResumeBet.svelte';
	import Sound from './Sound.svelte';
	import Background from './Background.svelte';
	import LoadingScreen from './LoadingScreen.svelte';
	import BoardFrame from './BoardFrame.svelte';
	import MultiplierGrid from './MultiplierGrid.svelte';
	import Board from './Board.svelte';
	import Anticipations from './Anticipations.svelte';
	import ClusterWinAmounts from './ClusterWinAmounts.svelte';
	import TumbleBoard from './TumbleBoard.svelte';
	import TumbleWinAmount from './TumbleWinAmount.svelte';
	import GlobalMultiplier from './GlobalMultiplier.svelte';
	import Win from './Win.svelte';
	import FreeSpinIntro from './FreeSpinIntro.svelte';
	import FreeSpinCounter from './FreeSpinCounter.svelte';
	import FreeSpinOutro from './FreeSpinOutro.svelte';
	import Transition from './Transition.svelte';
	import skin from '$skin/skin.generated';
	import { installFonts } from '../slots/fonts';

	const context = getContext();

	initBetModes();
	// Skin fonts + runtime bitmap fonts for win numbers (src/slots/fonts.ts); ready before the first win.
	installFonts();

	// Dev server only (tools\e2e reads and sets game state). Removed from production builds.
	if (import.meta.env.DEV) {
		(globalThis as any).__sv = {
			stateBet,
			stateConfig,
			stateModal,
			stateSession,
			isIdle: () => context.stateXstateDerived.isIdle(),
			loadingScreen: () => context.stateLayout.showLoadingScreen,
		};
	}

	onMount(() => (context.stateLayout.showLoadingScreen = true));

	context.eventEmitter.subscribeOnMount({
		buyBonusConfirm: () => {
			stateModal.modal = { name: 'buyBonusConfirm' };
		},
	});
</script>

<App>
	<EnableSound />
	<EnableHotkey />
	<EnableJurisdiction />
	<EnableGameActor />
	<EnablePixiExtension />

	<Background />

	{#if context.stateLayout.showLoadingScreen}
		<LoadingScreen onloaded={() => (context.stateLayout.showLoadingScreen = false)} />
	{:else}
		<ResumeBet />
		<!--
			The reason why <Sound /> is rendered after clicking the loading screen:
			"Autoplay with sound is allowed if: The user has interacted with the domain (click, tap, etc.)."
			Ref: https://developer.chrome.com/blog/autoplay
		-->
		<Sound />

		<MainContainer>
			<BoardFrame />
		</MainContainer>

		<MainContainer>
			<MultiplierGrid />
		</MainContainer>

		<MainContainer>
			<Board />
			<Anticipations />
			<TumbleWinAmount />
			<GlobalMultiplier />
		</MainContainer>

		<MainContainer>
			<TumbleBoard />
			<ClusterWinAmounts />
		</MainContainer>

		<UI>
			{#snippet gameName()}
				<UiGameName name={skin.rules.texts["game.name"] ?? skin.displayName.toUpperCase()} />
			{/snippet}
			<!-- Logo art comes with the final assets (instructions/19). Until then no second title:
				it overlapped the game name at popout S 400x225 (Engine [195]). -->
			{#snippet logo()}{/snippet}
		</UI>
		<Win />
		<FreeSpinIntro />
		{#if ['desktop', 'landscape'].includes(context.stateLayoutDerived.layoutType())}
			<FreeSpinCounter />
		{/if}
		<FreeSpinOutro />
		<Transition />

	{/if}
</App>

<GameModals>
	{#snippet version()}
		<GameVersion version={gameVersion} />
	{/snippet}
</GameModals>
