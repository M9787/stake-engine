// Session facts for the jurisdiction HUD (displaySessionTimer, displayNetPosition) and the
// minimumRoundDuration wait. Start values are set once, by the first authenticate.
export const stateSession = $state({
	startTime: Date.now(),
	startBalance: null as number | null,
	roundStart: null as number | null,
});

// jurisdiction.minimumRoundDuration. Engine docs do not state the unit (PROJECT.md §11 Q14).
// Read as milliseconds; a small value (under 100) can only mean seconds.
export const minimumRoundMs = (value: number | undefined) => {
	if (!value || value <= 0) return 0;
	return value < 100 ? value * 1000 : value;
};
