<script lang="ts">
	// Enforce jurisdiction flags from /wallet/authenticate (stored in stateConfig by <Authenticate />).
	// Shared UI buttons stay visible; their effect is reverted here. Hiding them needs a
	// components-ui-pixi change (PROJECT.md open question).
	import { stateBet, stateBetDerived, stateConfig } from 'state-shared';

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
</script>
