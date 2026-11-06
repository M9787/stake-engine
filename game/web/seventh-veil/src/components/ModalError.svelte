<script lang="ts" module>
	// RGS codes -> player message. Raw error JSON is never shown.
	// Engine codes (stake-engine.com/docs/rgs/wallet "Response codes", 2026-11-06): ERR_VAL, ERR_IPB,
	// ERR_GLE (400), ERR_ACT (429, retried by src/overrides/rgsFetcher.ts first), ERR_GEN (500).
	// ERR_PAUSED / ERR_RATE / ERR_BAD_REQUEST / ERR_NETWORK / ERR_NOT_FOUND are our names for
	// answers without an ERR_* body (423, 429 demo, plain 400, no connection, 404).
	const MESSAGES: Record<string, { text: string; closable: boolean }> = {
		ERR_IPB: { text: 'Insufficient balance. Lower your bet or add funds.', closable: true },
		ERR_VAL: { text: 'This request was not accepted. If it happens again, please reload the game.', closable: true },
		ERR_GLE: { text: 'Gambling limit reached.', closable: true },
		ERR_ACT: { text: 'The server is busy. Please try again in a moment.', closable: true },
		ERR_RATE: { text: 'Too many requests. Please wait a moment and try again.', closable: true },
		ERR_PAUSED: { text: 'New rounds are paused for maintenance. Please try again later.', closable: true },
		ERR_GEN: { text: 'Server error. Please reload the game to finish any open round.', closable: false },
		ERR_BAD_REQUEST: { text: 'The request could not be processed. Please reload the game.', closable: false },
		ERR_REPLAY: { text: 'This replay could not be loaded.', closable: false },
		ERR_NOT_FOUND: { text: 'This replay could not be found.', closable: false },
		ERR_BNF: { text: 'This replay could not be found.', closable: false },
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
