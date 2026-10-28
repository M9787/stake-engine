import _ from 'lodash';

import { stateBet, stateBetDerived, stateModal, stateUrlDerived } from 'state-shared';
import { checkIsMultipleRevealEvents } from 'utils-book';
import { createPrimaryMachines, createIntermediateMachines, createGameActor } from 'utils-xstate';

import type { Bet } from './typesBookEvent';
import { stateXstateDerived } from './stateXstate';
import { playBet, convertTorResumableBet } from './utils';
import { stateGameDerived } from './stateGame.svelte';

const primaryMachines = createPrimaryMachines<Bet>({
	onResumeGameActive: (betToResume) => convertTorResumableBet(betToResume),
	onResumeGameInactive: (betToResume) => {
		const lastRevealEvent = _.findLast(
			betToResume.state,
			(bookEvent) => bookEvent?.type === 'reveal',
		);

		if (lastRevealEvent) stateGameDerived.enhancedBoard.settle(lastRevealEvent.board);
	},
	onNewGameStart: async () => {
		// Engine [222]: no /wallet/play without the balance for the mode's real cost. Runs before
		// every play request (button, Space press and hold, autoplay, bonus buy), so the request
		// never leaves the browser and the player sees why.
		if (!stateBetDerived.isBetCostAvailable()) {
			stateBet.autoSpinsCounter = 0;
			stateModal.modal = { name: 'error', error: { error: 'ERR_IPB', message: 'insufficient balance' } };
			throw new Error('insufficient balance: play request not sent');
		}
		if ((stateBet.isTurbo && stateXstateDerived.isAutoBetting()) || stateBet.isSpaceHold) return;
		stateBet.winBookEventAmount = 0;
		await stateGameDerived.enhancedBoard.preSpin({});
	},
	onNewGameError: () => stateGameDerived.enhancedBoard.settle(),
	onPlayGame: async (bet) => {
		await playBet(bet);
		// A bonus buy is one round. Back to the base mode so the bet label and checks show the
		// next spin's cost (ButtonBetProvider does the same on the next press). Replay keeps
		// the mode to show its real cost.
		if (!stateUrlDerived.replay() && stateBetDerived.activeBetMode()?.type === 'buy') {
			stateBet.activeBetModeKey = 'BASE';
		}
	},
	checkIsBonusGame: (bet) => checkIsMultipleRevealEvents({ bookEvents: bet.state }),
});

const intermediateMachines = createIntermediateMachines(primaryMachines);

export const gameActor = createGameActor(intermediateMachines);
