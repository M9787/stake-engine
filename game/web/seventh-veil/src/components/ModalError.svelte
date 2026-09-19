<script lang="ts" module>
	// RGS status codes (rgs-fetcher schema) -> player message. Raw error JSON is never shown.
	const MESSAGES: Record<string, { text: string; closable: boolean }> = {
		ERR_IPB: { text: 'Insufficient balance. Lower your bet or add funds.', closable: true },
		ERR_VAL: { text: 'That bet is not available. Please choose another bet.', closable: true },
		ERR_IS: { text: 'Your session has expired. Please reload the game.', closable: false },
		ERR_ATE: { text: 'Your session has expired. Please reload the game.', closable: false },
		ERR_GLE: { text: 'Gambling limit reached.', closable: false },
		ERR_REPLAY: { text: 'This replay could not be loaded.', closable: false },
	};
	const FALLBACK = { text: 'Connection problem. Please reload the game.', closable: false };

	export const errorCode = (error: unknown): string => {
		const e = error as { error?: unknown; statusCode?: unknown; status?: { statusCode?: unknown } } | null;
		const code = e?.error ?? e?.statusCode ?? e?.status?.statusCode;
		return typeof code === 'string' ? code : 'UNKNOWN';
	};
	export const errorMessage = (error: unknown) => MESSAGES[errorCode(error)] ?? FALLBACK;
</script>

<script lang="ts">
	import { Popup } from 'components-shared';
	import { zIndex } from 'constants-shared/zIndex';
	import { stateModal } from 'state-shared';
	import BaseContent from 'components-ui-html/src/components/BaseContent.svelte';
	import { t } from '../game/wording';
</script>

{#if stateModal.modal?.name === 'error'}
	{@const info = errorMessage(stateModal.modal?.error)}
	<Popup zIndex={zIndex.modal} persistent={!info.closable} onclose={() => (stateModal.modal = null)}>
		<BaseContent maxWidth="100%">
			<p class="error-text">{t(info.text)}</p>
			<small class="error-code">Code: {errorCode(stateModal.modal?.error)}</small>
		</BaseContent>
	</Popup>
{/if}

<style lang="scss">
	.error-text {
		max-width: 420px;
		white-space: normal;
		text-align: center;
		margin: 0 0 0.5rem;
	}
	.error-code {
		opacity: 0.6;
	}
</style>
