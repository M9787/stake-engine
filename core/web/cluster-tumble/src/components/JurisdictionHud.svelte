<!--
	Jurisdiction HUD: a thin top-left line shown only when the RGS asks for it in
	authenticate config.jurisdiction:
	- displaySessionTimer: time since the game opened;
	- displayNetPosition: balance now minus balance at the start of the session;
	- displayRTP: the game RTP (the rules always show RTP per mode, Engine [25]).
-->
<script lang="ts">
	import { onDestroy } from 'svelte';
	import { stateBet, stateConfig, stateUrlDerived } from 'state-shared';
	import { numberToCurrencyString } from 'utils-shared/amount';

	import config from '$skin/config';
	import { stateSession } from '../game/stateSession.svelte';

	let now = $state(Date.now());
	const timer = setInterval(() => (now = Date.now()), 1000);
	onDestroy(() => clearInterval(timer));

	const jurisdiction = $derived(stateConfig.jurisdiction);
	const pad = (value: number) => String(value).padStart(2, '0');

	const elapsed = $derived.by(() => {
		const seconds = Math.max(0, Math.floor((now - stateSession.startTime) / 1000));
		return `${pad(Math.floor(seconds / 3600))}:${pad(Math.floor((seconds % 3600) / 60))}:${pad(seconds % 60)}`;
	});

	const net = $derived.by(() => {
		if (stateSession.startBalance === null) return null;
		const value = stateBet.balanceAmount - stateSession.startBalance;
		const text = numberToCurrencyString(Math.abs(value));
		return value < 0 ? `−${text}` : `+${text}`;
	});

	const parts = $derived(
		[
			jurisdiction?.displaySessionTimer ? `Session ${elapsed}` : null,
			jurisdiction?.displayNetPosition && net !== null ? `Net ${net}` : null,
			jurisdiction?.displayRTP ? `RTP ${(config.rtp * 100).toFixed(2)}%` : null,
		].filter(Boolean),
	);
</script>

{#if parts.length && !stateUrlDerived.replay()}
	<div class="hud" aria-live="off">{parts.join(' · ')}</div>
{/if}

<style>
	.hud {
		position: fixed;
		top: 2.2em;
		left: 0.6em;
		z-index: 10;
		padding: 0.15em 0.5em;
		border-radius: 0.3em;
		background: rgba(0, 0, 0, 0.55);
		color: #fff;
		font: 600 12px/1.4 Inter, sans-serif;
		pointer-events: none;
		white-space: nowrap;
	}
</style>
