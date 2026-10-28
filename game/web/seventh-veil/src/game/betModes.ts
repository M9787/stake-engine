import { stateBet, stateMeta, type BetModeData, type BetModeMeta } from 'state-shared';

import config from './config';
import { t } from './wording';

// Keys follow the SDK convention (upper case). Math mode names are the lower-case versions.
// No external asset URLs: Engine builds may not load anything from outside the bundle.
const noAssets = { icon: '', volatility: '', button: '', dialogImage: '', dialogVolatility: '' };

const mode = (
	key: string,
	mathName: keyof typeof config.betModes,
	type: BetModeData['type'],
	title: string,
	dialog: string,
): BetModeData => ({
	mode: key,
	costMultiplier: config.betModes[mathName].cost,
	type,
	parent: '',
	children: '',
	maxWin: config.betModes[mathName].max_win,
	assets: noAssets,
	text: {
		title: t(title),
		dialog: t(dialog),
		button: type === 'buy' ? t('BUY') : type === 'activate' ? 'ACTIVATE' : '',
		// Shared LabelBet falls back to the spin-button text ("SPIN" in social mode); name the
		// amount itself instead (Engine [77]).
		betAmountLabel: t('BET'),
		tickerIdle: '',
		tickerSpin: '',
		bannerText: '',
	},
});

const rtpText = (mathName: keyof typeof config.betModes) =>
	`RTP ${(config.betModes[mathName].rtp * 100).toFixed(2)}%. Max win ${config.betModes[mathName].max_win.toLocaleString('en-US')}x.`;

// Built at init (after authenticate) so social-casino wording can apply.
const buildBetModes = (): BetModeMeta => ({
	BASE: mode('BASE', 'base', 'default', 'FATE: VEIL', `Standard play. Bonus about 1 in 400 spins. Every winning spin pays more than the bet. ${rtpText('base')}`),
	OMEN: mode(
		'OMEN',
		'omen',
		'activate',
		'FATE: OMEN',
		`Price 1.25x per spin. Bonus about 1 in 150 spins instead of 1 in 400. Many wins return less than the spin price. ${rtpText('omen')}`,
	),
	PROPHECY: mode(
		'PROPHECY',
		'prophecy',
		'activate',
		'FATE: PROPHECY',
		`Price 2x per spin. Bonus about 1 in 80 spins. Many wins return less than the spin price. ${rtpText('prophecy')}`,
	),
	STAR: mode(
		'STAR',
		'star',
		'buy',
		'STAR BONUS',
		`12-15 free spins. Starts with 5 spots charged at x2; sigils persist for the whole bonus. Can pay less than its price. ${rtpText('star')}`,
	),
	TOWER: mode(
		'TOWER',
		'tower',
		'buy',
		'TOWER BONUS',
		`15-18 free spins. Starts with 12 spots charged at x2. Can pay less than its price. ${rtpText('tower')}`,
	),
});

export let SEVENTH_VEIL_BET_MODES: BetModeMeta = buildBetModes();

export const initBetModes = () => {
	SEVENTH_VEIL_BET_MODES = buildBetModes();
	stateMeta.betModeMeta = SEVENTH_VEIL_BET_MODES;
};

/** Full cost of the active mode in base-bet multiples (buy modes included). */
export const activeModeCost = () =>
	SEVENTH_VEIL_BET_MODES[stateBet.activeBetModeKey.toUpperCase()]?.costMultiplier ?? 1;

/**
 * Celebrate only a real win: payout strictly above what the round cost.
 * `amount` is a book amount (multiplier x 100). See docs/08-compliance.md.
 */
export const isCelebratedWin = (amount: number) => amount / 100 > activeModeCost();
