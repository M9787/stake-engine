import { stateBet, stateMeta, type BetModeData, type BetModeMeta } from 'state-shared';

import skin from '$skin/skin.generated';
import { t } from './wording';

// Modes, titles and dialog texts come from the skin (tools/gen/gen_rules.py): numbers are filled from
// game.json and the published math, never typed here. Keys follow the SDK convention (upper case).
// No external asset URLs: Engine builds may not load anything from outside the bundle.
const noAssets = { icon: '', volatility: '', button: '', dialogImage: '', dialogVolatility: '' };

type SkinMode = (typeof skin.rules.modes)[number];

const mode = (m: SkinMode): BetModeData => ({
	mode: m.key,
	costMultiplier: m.cost,
	type: m.type as BetModeData['type'],
	parent: '',
	children: '',
	maxWin: m.maxWin ?? 0,
	assets: noAssets,
	text: {
		title: t(m.title),
		dialog: t(m.dialog),
		button: m.type === 'buy' ? t('BUY') : m.type === 'activate' ? 'ACTIVATE' : '',
		// Shared LabelBet falls back to the spin-button text ("SPIN" in social mode); name the
		// amount itself instead (Engine [77]).
		betAmountLabel: t('BET'),
		tickerIdle: '',
		tickerSpin: '',
		bannerText: '',
	},
});

// Built at init (after authenticate) so social-casino wording can apply.
const buildBetModes = (): BetModeMeta => Object.fromEntries(skin.rules.modes.map((m) => [m.key, mode(m)]));

export let BET_MODES: BetModeMeta = buildBetModes();

export const initBetModes = () => {
	BET_MODES = buildBetModes();
	stateMeta.betModeMeta = BET_MODES;
};

/** Full cost of the active mode in base-bet multiples (buy modes included). */
export const activeModeCost = () =>
	BET_MODES[stateBet.activeBetModeKey.toUpperCase()]?.costMultiplier ?? 1;

/**
 * Celebrate only a real win: payout strictly above what the round cost.
 * `amount` is a book amount (multiplier x 100). See docs/08-compliance.md.
 */
export const isCelebratedWin = (amount: number) => amount / 100 > activeModeCost();
