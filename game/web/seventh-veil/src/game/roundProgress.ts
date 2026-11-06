// Bonus resume (Engine: stake-engine.com/docs/rgs "API flows", 2026-11-06).
// During a bonus we record the index of the free spin being shown with POST /bet/event.
// After a reload, /wallet/authenticate returns the open round with round.event = that index,
// and convertTorResumableBet (utils.ts) restarts the animation from that free spin.
// The value is the book event index as a string (a few bytes).
import { requestEndEvent } from 'rgs-requests';
import { stateUrlDerived } from 'state-shared';

export const recordRoundProgress = (eventIndex: number) => {
	// Replays never touch the player's session.
	if (stateUrlDerived.replay()) return;
	// Fire and forget: a failed record only means a resume starts a little earlier.
	void requestEndEvent({
		rgsUrl: stateUrlDerived.rgsUrl(),
		sessionID: stateUrlDerived.sessionID(),
		eventIndex,
	}).catch(() => undefined);
};
