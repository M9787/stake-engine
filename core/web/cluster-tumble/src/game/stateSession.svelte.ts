// Session facts for the jurisdiction HUD (displaySessionTimer, displayNetPosition) and the
// minimumRoundDuration wait. Start values are set once, by the first authenticate.
export const stateSession = $state({
	startTime: Date.now(),
	startBalance: null as number | null,
	roundStart: null as number | null,
	// All bet levels from authenticate (dollars) and each mode's own maxBet (dollars, upper-case
	// mode key) from config.gameModes (stake-engine.com/docs/rgs/wallet, 2026-11-06).
	allBetLevels: [] as number[],
	modeMaxBet: {} as Record<string, number>,
});

/** Bet levels allowed in a mode: levels up to the mode's maxBet; all levels if none is set. */
export const betLevelsForMode = (modeKey: string) => {
	const max = stateSession.modeMaxBet[modeKey.toUpperCase()];
	if (!max) return stateSession.allBetLevels;
	const allowed = stateSession.allBetLevels.filter((level) => level <= max + 1e-9);
	return allowed.length ? allowed : stateSession.allBetLevels.slice(0, 1);
};

// jurisdiction.minimumRoundDuration. Engine docs do not state the unit (PROJECT.md §11 Q14).
// Read as milliseconds; a small value (under 100) can only mean seconds.
export const minimumRoundMs = (value: number | undefined) => {
	if (!value || value <= 0) return 0;
	return value < 100 ? value * 1000 : value;
};
