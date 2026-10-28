<!--
	Seventh Veil copy of components-shared Authenticate.svelte (web-sdk packages are read-only).
	Changes vs the shared version:
	- starting bet = config.defaultBetLevel (shared version ignores it and starts at 1);
	- betLevels missing -> build levels from minBet..maxBet in stepBet steps;
	- jurisdiction always an object; social=true URL param also sets socialCasino;
	- no raw objects in the console.
-->
<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import { page } from '$app/state';

	import { requestAuthenticate, requestReplay } from 'rgs-requests';
	import { stateUrlDerived, stateBet, stateConfig, stateModal, stateUi } from 'state-shared';
	import { API_AMOUNT_MULTIPLIER, MOST_USED_BET_INDEXES } from 'constants-shared/bet';

	import { stateReplay } from '../game/stateReplay.svelte';

	type Props = { children: Snippet };

	const props: Props = $props();

	let authenticated = $state(false);

	// Bet levels in API units. Falls back to minBet..maxBet in stepBet steps (RGS rules).
	const betLevels = (cfg: any): number[] => {
		if (cfg?.betLevels?.length) return cfg.betLevels;
		const { minBet, maxBet, stepBet } = cfg || {};
		if (!minBet || !maxBet || !stepBet) return [];
		const levels: number[] = [];
		for (let v = minBet; v <= maxBet && levels.length < 200; v += stepBet) levels.push(v);
		return levels;
	};

	const authenticate = async () => {
		try {
			const authenticateData = await requestAuthenticate({
				rgsUrl: stateUrlDerived.rgsUrl(),
				sessionID: stateUrlDerived.sessionID(),
				language: stateUrlDerived.lang(),
			});

			// error
			if (authenticateData?.error) throw authenticateData;

			// balance
			if (authenticateData?.balance) {
				// Example of authenticateData.balance
				// {
				// 		"amount": 10000000000000000,
				// 		"currency": "USD"
				// },
				stateBet.currency = authenticateData.balance.currency;
				stateBet.balanceAmount = authenticateData.balance.amount / API_AMOUNT_MULTIPLIER;
			}

			// config
			if (authenticateData?.config) {
				// Example of authenticateData.config
				// {
				// 	"gameID": "37_test-lines",
				// 	"minBet": 100000,
				// 	"maxBet": 1000000000,
				// 	"stepBet": 10000,
				// 	"defaultBetLevel": 1000000,
				// 	"betLevels": [100000, 200000, ..., 1000000000],
				// 	"betModes": {},
				// 	"jurisdiction": {
				// 			"socialCasino": false,
				// 			"disabledFullscreen": false,
				// 			"disabledTurbo": false,
				// 			"disabledSuperTurbo": false,
				// 			"disabledAutoplay": false,
				// 			"disabledSlamstop": false,
				// 			"disabledSpacebar": false,
				// 			"disabledBuyFeature": false,
				// 			"displayNetPosition": false,
				// 			"displayRTP": false,
				// 			"displaySessionTimer": false,
				// 			"minimumRoundDuration": 0
				// 	}
				// }
				const cfg = authenticateData.config;
				stateConfig.jurisdiction = {
					...(cfg.jurisdiction || {}),
					socialCasino: !!cfg.jurisdiction?.socialCasino || stateUrlDerived.social(),
				} as typeof stateConfig.jurisdiction;
				stateConfig.betAmountOptions = betLevels(cfg).map((level) => level / API_AMOUNT_MULTIPLIER);
				if (cfg.defaultBetLevel && stateConfig.betAmountOptions.length) {
					const wanted = cfg.defaultBetLevel / API_AMOUNT_MULTIPLIER;
					stateBet.betAmount = stateConfig.betAmountOptions.reduce((best, level) =>
						Math.abs(level - wanted) < Math.abs(best - wanted) ? level : best,
					);
				} else if (stateConfig.betAmountOptions.length) {
					stateBet.betAmount = stateConfig.betAmountOptions[0];
				}
				stateConfig.betMenuOptions = stateConfig.betAmountOptions.filter((_, index) =>
					MOST_USED_BET_INDEXES.includes(index),
				);
			}

			// round
			if (authenticateData?.round) {
				// Example of authenticateData.round 
				// {
				// 	"betID": 62277967,
				// 	"amount": 1000000,
				// 	"payout": 33400000,
				// 	"payoutMultiplier": 33.4,
				// 	"active": true,
				// 	"state": [...],
				// 	"mode": "BONUS",
				// 	"event": null
				// }

				if(authenticateData.round?.state) {
					// @ts-ignore
					stateBet.betToResume =  authenticateData.round;
				}

				if(authenticateData.round?.amount) {
					const betAmountValue =
						authenticateData.round.amount > 0
							? authenticateData.round.amount / API_AMOUNT_MULTIPLIER
							: 0;
					stateBet.betAmount = betAmountValue;
					stateBet.wageredBetAmount = betAmountValue;
				}

				if (authenticateData.round?.mode) {
					stateBet.activeBetModeKey = authenticateData.round.mode;
				};
			}
		} catch (error) {
			stateModal.modal = { name: 'error', error };
		}
	};

	// Replay has no session, so authenticate never runs: currency and bet come from the URL
	// (Engine [172]). Bad or missing values fall back instead of breaking the replay.
	const replayCurrency = () => {
		const raw = (page.url.searchParams.get('currency') || '').toUpperCase();
		return /^[A-Z]{3,5}$/.test(raw) ? raw : 'USD';
	};
	const replayBetAmount = () => {
		const amount = stateUrlDerived.amount() / API_AMOUNT_MULTIPLIER;
		return Number.isFinite(amount) && amount > 0 ? amount : 1;
	};

	const handleReplay = async () => {
		stateBet.currency = replayCurrency();
		stateBet.betAmount = replayBetAmount();
		stateBet.wageredBetAmount = replayBetAmount();
		stateBet.activeBetModeKey = stateUrlDerived.mode();

		const data = await requestReplay({
			rgsUrl: stateUrlDerived.rgsUrl(),
			game: stateUrlDerived.game(),
			mode: stateUrlDerived.mode(),
			version: stateUrlDerived.version(),
			event: stateUrlDerived.event(),
		});

		if (!data || (data as any).error || !(data as any).state) {
			stateModal.modal = { name: 'error', error: { error: 'ERR_REPLAY', message: 'replay not found' } };
			return;
		}
		if(data) {
			// @ts-ignore
			stateBet.betToResume = {
				...data,
				event: '0',
				active: true,
				mode: stateUrlDerived.mode(),
			};
			stateReplay.round = { ...stateBet.betToResume };
			stateReplay.costMultiplier = Number((data as any).costMultiplier) || 1;
		}
	};

	onMount(async () => {
		if(stateUrlDerived.replay()) {
			stateUi.config.mode = 'replay';
			try {
				await handleReplay();
			} catch (error) {
				stateModal.modal = { name: 'error', error: { error: 'ERR_REPLAY', message: 'replay could not load' } };
			}
		} else {
			stateUi.config.mode = 'default';
			await authenticate();
		};

		authenticated = true;
	});
</script>

{#if authenticated}
	{@render props.children()}
{/if}
