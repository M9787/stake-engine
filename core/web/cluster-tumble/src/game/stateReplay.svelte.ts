import type { BetToResume } from 'state-shared';

// The replayed round as loaded from /bet/replay. The resume machine clears
// stateBet.betToResume after one play, so "Replay again" (Engine [173]) restores this copy.
export const stateReplay = $state({
	round: null as BetToResume,
	costMultiplier: 1,
});
