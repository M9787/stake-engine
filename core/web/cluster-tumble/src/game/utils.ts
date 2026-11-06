import _ from 'lodash';
import { stateBet } from 'state-shared';
import { createPlayBookUtils } from 'utils-book';
import { createGetEmptyPaddedBoard } from 'utils-slots';

import skin from '$skin/skin.generated';

import { SYMBOL_SIZE, REEL_PADDING, BOARD_DIMENSIONS } from './constants';
import { eventEmitter } from './eventEmitter';
import type { Bet, BookEventOfType } from './typesBookEvent';
import { bookEventHandlerMap } from './bookEventHandlerMap';
import type { RawSymbol, SymbolState } from './types';

// general utils
export const { getEmptyBoard } = createGetEmptyPaddedBoard({ reelsDimensions: BOARD_DIMENSIONS });
export const { playBookEvent, playBookEvents } = createPlayBookUtils({ bookEventHandlerMap });
export const playBet = async (bet: Bet) => {
	stateBet.winBookEventAmount = 0;
	await playBookEvents(bet.state);
	eventEmitter.broadcast({ type: 'stopButtonEnable' });
};

// resume bet
const BOOK_EVENT_TYPES_TO_RESERVE_FOR_SNAPSHOT = [
	'bonusVariant',
	'updateGrid',
	'freeSpinTrigger',
	'updateFreeSpin',
	'setTotalWin',
];

export const convertTorResumableBet = (betToResume: Bet) => {
	const resumingIndex = Number(betToResume.event);
	const bookEventsBeforeResume = betToResume.state.filter(
		(_, eventIndex) => eventIndex < resumingIndex,
	);
	const bookEventsAfterResume = betToResume.state.filter(
		(_, eventIndex) => eventIndex >= resumingIndex,
	);

	const bookEventToCreateSnapshot: BookEventOfType<'createBonusSnapshot'> = {
		index: 0,
		type: 'createBonusSnapshot',
		bookEvents: bookEventsBeforeResume.filter((bookEvent) =>
			BOOK_EVENT_TYPES_TO_RESERVE_FOR_SNAPSHOT.includes(bookEvent.type),
		),
	};

	const stateToResume = [bookEventToCreateSnapshot, ...bookEventsAfterResume];

	return { ...betToResume, state: stateToResume };
};

// other utils
export const getSymbolX = (reelIndex: number) => SYMBOL_SIZE * (reelIndex + REEL_PADDING);
export const getSymbolY = (symbolIndexOfBoard: number) => (symbolIndexOfBoard + 0.5) * SYMBOL_SIZE;

// Symbol look per state (plan v3.3 slice 10.6b): one image per symbol (slot symbol.<id>) moved by a
// motion preset. 'motion' states take time and call oncomplete when done; 'static' states complete at once.
const SYMBOL_ROLES: Record<string, string> = Object.fromEntries(skin.symbols.map((s) => [s.id, s.role]));

export const getSymbolInfo = ({ rawSymbol, state }: { rawSymbol: RawSymbol; state: SymbolState }) => {
	const role = SYMBOL_ROLES[rawSymbol.name] ?? 'pay';
	const preset =
		state === 'win' ? 'pulse' : state === 'explosion' ? 'dissolve' : state === 'land' && role === 'scatter' ? 'land' : 'static';
	return {
		type: preset === 'static' ? ('static' as const) : ('motion' as const),
		preset,
		role,
		sizeRatio: role === 'scatter' ? 1.15 : 1,
	};
};
