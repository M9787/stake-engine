import _ from 'lodash';
import type { Tween } from 'svelte/motion';

import { stateBet } from 'state-shared';
import { createEnhanceBoard, createReelForCascading } from 'utils-slots';
import { createGetWinLevelDataByWinLevelAlias } from 'utils-shared/winLevel';

import type { GameType, RawSymbol, SymbolState } from './types';
import { stateLayoutDerived } from './stateLayout';
import { winLevelMap } from './winLevelMap';
import { eventEmitter } from './eventEmitter';
import {
	SYMBOL_SIZE,
	BOARD_SIZES,
	INITIAL_BOARD,
	BOARD_DIMENSIONS,
	SPIN_OPTIONS_DEFAULT,
	SPIN_OPTIONS_FAST,
	INITIAL_SYMBOL_STATE,
	SCATTER_LAND_SOUND_MAP,
} from './constants';

const onSymbolLand = ({ rawSymbol }: { rawSymbol: RawSymbol }) => {
	if (rawSymbol.name === 'S') {
		eventEmitter.broadcast({ type: 'soundScatterCounterIncrease' });
		eventEmitter.broadcast({
			type: 'soundOnce',
			name: SCATTER_LAND_SOUND_MAP[scatterLandIndex()],
		});
	}

	if (rawSymbol.name === 'W') {
		eventEmitter.broadcast({
			type: 'soundOnce',
			name: 'sfx_multiplier_landing',
		});
	}
};

const board = _.range(BOARD_DIMENSIONS.x).map((reelIndex) => {
	const reel = createReelForCascading({
		reelIndex,
		symbolHeight: SYMBOL_SIZE,
		initialSymbols: INITIAL_BOARD[reelIndex],
		initialSymbolState: INITIAL_SYMBOL_STATE,
		onReelStopping: () => {
			eventEmitter.broadcast({
				type: 'soundOnce',
				name: 'sfx_reel_stop_1',
				forcePlay: !stateBet.isTurbo,
			});
		},
		onSymbolLand,
	});

	reel.reelState.spinOptions = () =>
		reel.reelState.spinType === 'fast' ? SPIN_OPTIONS_FAST : SPIN_OPTIONS_DEFAULT;

	return reel;
});

export type Reel = (typeof board)[number];
export type ReelSymbol = Reel['reelState']['symbols'][number];

export type TumbleSymbol = {
	symbolY: Tween<number>;
	rawSymbol: RawSymbol;
	symbolState: SymbolState;
	oncomplete: () => void;
};

export type MultiplierSymbol = {
	initX: number;
	initY: number;
	symbolX: Tween<number>;
	symbolY: Tween<number>;
	rawSymbol: RawSymbol;
	symbolState: SymbolState;
	oncomplete: () => void;
};

export const stateGame = $state({
	board,
	gameType: 'basegame' as GameType,
	tumbleBoardAdding: [] as TumbleSymbol[][],
	tumbleBoardBase: [] as TumbleSymbol[][],
	multiplierBoard: [] as (MultiplierSymbol | undefined)[][],
	scatterCounter: 0,
	bonusVariant: null as string | null, // a bonus variant id from game.json features.bonusVariants
	gridAtCap: false,
});

// Board centre height per layout, as a share of the main layout height. The HUD sits at the
// bottom (balance/win/bet panels), so the 7x7 board sits above centre and the bottom row stays
// clear of it at 1280x720, 1200x675, 400x225 and 425x812 (tools\e2e shots, docs/10 M6c).
const BOARD_CENTRE_Y = { desktop: 0.4, landscape: 0.41, tablet: 0.4, portrait: 0.4 } as const;

const boardLayout = () => ({
	x: stateLayoutDerived.mainLayout().width * 0.5,
	y:
		stateLayoutDerived.mainLayout().height *
		(BOARD_CENTRE_Y[stateLayoutDerived.layoutType() as keyof typeof BOARD_CENTRE_Y] ?? 0.4),
	anchor: { x: 0.5, y: 0.5 },
	pivot: { x: BOARD_SIZES.width / 2, y: BOARD_SIZES.height / 2 },
	...BOARD_SIZES,
});

const boardRaw = () =>
	board.map((reel) => reel.reelState.symbols.map((reelSymbol) => reelSymbol.rawSymbol));

const tumbleBoardCombined = () => {
	const tumbleBoardCombined = stateGame.tumbleBoardBase.map((tumbleReelBase, reelIndex) => {
		const tumbleReelAdding = stateGame.tumbleBoardAdding[reelIndex] ?? [];
		return [...tumbleReelAdding, ...tumbleReelBase];
	});

	return tumbleBoardCombined;
};

const scatterLandIndex = () => {
	if (stateGame.scatterCounter > 5) return 5;
	if (stateGame.scatterCounter < 1) return 1;
	return stateGame.scatterCounter as 1 | 2 | 3 | 4 | 5;
};

const { enhanceBoard } = createEnhanceBoard();
const enhancedBoard = enhanceBoard({ board: stateGame.board });

// win levels

export const { getWinLevelDataByWinLevelAlias } = createGetWinLevelDataByWinLevelAlias({
	winLevelMap,
});

export const stateGameDerived = {
	onSymbolLand,
	boardLayout,
	boardRaw,
	tumbleBoardCombined,
	scatterLandIndex,
	enhancedBoard,
	getWinLevelDataByWinLevelAlias,
};
