<script lang="ts">
	// Same modal set as components-ui-html <Modals />, but with Seventh Veil's own
	// pay table and game rules (the shared ones are "ADD YOUR ..." stubs).
	import type { Snippet } from 'svelte';

	import { Popup } from 'components-shared';
	import { zIndex } from 'constants-shared/zIndex';
	import { stateConfig, stateModal } from 'state-shared';
	import ModalError from './ModalError.svelte';
	import ModalBetMenu from 'components-ui-html/src/components/ModalBetMenu.svelte';
	import ModalBuyBonus from 'components-ui-html/src/components/ModalBuyBonus.svelte';
	import ModalBuyBonusConfirm from 'components-ui-html/src/components/ModalBuyBonusConfirm.svelte';
	import ModalAutoSpin from 'components-ui-html/src/components/ModalAutoSpin.svelte';
	import ModalAutoSpinMessage from 'components-ui-html/src/components/ModalAutoSpinMessage.svelte';
	import ModalSettings from 'components-ui-html/src/components/ModalSettings.svelte';
	import BaseContent from 'components-ui-html/src/components/BaseContent.svelte';
	import BaseScrollable from 'components-ui-html/src/components/BaseScrollable.svelte';

	import GameInfo from './GameInfo.svelte';

	type Props = { version: Snippet };
	const props: Props = $props();
</script>

<ModalError />
<ModalBetMenu />
{#if !stateConfig.jurisdiction?.disabledBuyFeature}
	<ModalBuyBonus />
	<ModalBuyBonusConfirm />
{/if}
{#if !stateConfig.jurisdiction?.disabledAutoplay}
	<ModalAutoSpin />
	<ModalAutoSpinMessage />
{/if}
<ModalSettings />

{#if stateModal.modal?.name === 'payTable' || stateModal.modal?.name === 'gameRules'}
	<Popup zIndex={zIndex.modal} onclose={() => (stateModal.modal = null)}>
		<BaseContent maxWidth="100%">
			<BaseScrollable type="column">
				<GameInfo section={stateModal.modal.name === 'payTable' ? 'payTable' : 'gameRules'} />
				{@render props.version()}
			</BaseScrollable>
		</BaseContent>
	</Popup>
{/if}
