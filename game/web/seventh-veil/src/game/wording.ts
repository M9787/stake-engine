import { stateConfig, stateUrlDerived } from 'state-shared';

// Social casino (stake.us) wording. Source: restricted phrases and suggested replacements,
// https://stake-engine.com/docs/approval-guidelines/jurisdiction-requirements (checked 2026-09-19).
// Longer phrases first so "bonus buy" wins over "buy".
const SWEEPS: [string, string][] = [
	["be awarded to player's accounts", "appear in player's accounts"],
	['place your bets', 'come and play'],
	['at the cost of', 'for'],
	['cost of', 'can be played for'],
	['win feature', 'play feature'],
	['buy bonus', 'get bonus'],
	['bonus buy', 'bonus'],
	['total bet', 'total play'],
	['pays out', 'wins'],
	['paid out', 'won'],
	['pay out', 'win'],
	['betting', 'playing'],
	['bought', 'instantly triggered'],
	['purchase', 'play'],
	['currency', 'token'],
	['withdraw', 'redeem'],
	['deposit', 'get coins'],
	['gamble', 'play'],
	['wager', 'play'],
	['credit', 'balance'],
	['rebet', 'respin'],
	['money', 'coins'],
	['stake', 'play amount'],
	['payer', 'winner'],
	['cash', 'coins'],
	['fund', 'balance'],
	['bets', 'plays'],
	['bet', 'play'],
	['buy', 'play'],
	['pays', 'wins'],
	['paid', 'won'],
	['pay', 'win'],
];

const matchCase = (source: string, target: string) => {
	if (source === source.toUpperCase()) return target.toUpperCase();
	if (source[0] === source[0].toUpperCase()) return target[0].toUpperCase() + target.slice(1);
	return target;
};

const PATTERN = new RegExp(`\\b(${SWEEPS.map(([from]) => from.replace(/'/g, "['’]")).join('|')})\\b`, 'gi');
const LOOKUP = new Map(SWEEPS.map(([from, to]) => [from, to]));

/** True when the game runs in a social casino: URL `social=true` or jurisdiction flag. */
export const isSocial = () => stateUrlDerived.social() || !!stateConfig.jurisdiction?.socialCasino;

/** Replace restricted gambling terms with the social-casino phrase. */
export const toSweeps = (text: string) =>
	text.replace(PATTERN, (hit) => matchCase(hit, LOOKUP.get(hit.toLowerCase().replace('’', "'")) ?? hit));

/** Player-facing text: unchanged normally, sweeps wording in a social casino. */
export const t = (text: string) => (isSocial() ? toSweeps(text) : text);
