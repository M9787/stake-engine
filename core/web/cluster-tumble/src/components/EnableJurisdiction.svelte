<script lang="ts">
	// Enforce jurisdiction flags from /wallet/authenticate (stored in stateConfig by <Authenticate />).
	// Shared UI buttons stay visible; their effect is reverted here. Hiding them needs a
	// components-ui-pixi change (PROJECT.md open question).
	import { stateBet, stateBetDerived, stateConfig } from 'state-shared';
	import { MOST_USED_BET_INDEXES } from 'constants-shared/bet';

	import { stateSession, betLevelsForMode } from '../game/stateSession.svelte';

	// Reduced motion (OS setting prefers-reduced-motion): start in turbo, which shortens the
	// animations; results are the same. The player can still switch it off. Not where the
	// jurisdiction disables turbo (next effect).
	if (
		typeof matchMedia === 'function' &&
		matchMedia('(prefers-reduced-motion: reduce)').matches &&
		!stateConfig.jurisdiction.disabledTurbo
	) {
		stateBetDerived.updateIsTurbo(true, { persistent: false });
	}

	$effect(() => {
		if (stateConfig.jurisdiction.disabledTurbo && stateBet.isTurbo) {
			stateBetDerived.updateIsTurbo(false, { persistent: true });
		}
	});

	$effect(() => {
		if (stateConfig.jurisdiction.disabledAutoplay && stateBet.autoSpinsCounter > 0) {
			stateBet.autoSpinsCounter = 0;
		}
	});

	$effect(() => {
		if (stateConfig.jurisdiction.disabledBuyFeature && stateBetDerived.activeBetMode()?.type === 'buy') {
			stateBet.activeBetModeKey = 'BASE';
		}
	});

	// config.gameModes[].maxBet: each mode offers only bet levels up to its own maxBet, and a bet
	// above it drops to the highest allowed level when the mode changes. Replay has no levels.
	$effect(() => {
		const modeKey = stateBet.activeBetModeKey;
		if (!stateSession.allBetLevels.length) return;
		const levels = betLevelsForMode(modeKey);
		if (levels.join() !== stateConfig.betAmountOptions.join()) {
			stateConfig.betAmountOptions = levels;
			stateConfig.betMenuOptions = levels.filter((_, index) => MOST_USED_BET_INDEXES.includes(index));
		}
		const max = levels[levels.length - 1];
		if (stateBet.betAmount > max) stateBet.betAmount = max;
	});
</script>
