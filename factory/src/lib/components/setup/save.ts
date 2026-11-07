// Client helpers for the Setup page (routes/game/[id]/setup). Server side: lib/server/setup.ts.
import type { ValidateResult } from '$lib/types';
import { api, sendJson } from '$lib/components/JobPanel.svelte';

export type SaveResult = { validation: ValidateResult; snapshot: string | null };

/** PUT one Advanced form; throws Error with a plain message. */
export const saveSection = (game: string, section: string, payload: Record<string, unknown>) =>
	api<SaveResult>(`/api/game/${encodeURIComponent(game)}/setup`, sendJson('PUT', { section, ...payload }));

/** Deep copy of server data for a local form (plain JSON only). */
export const copy = <T>(v: T): T => JSON.parse(JSON.stringify(v));

/** Read a number input; keeps the old value when the box is empty or not a number. */
export const toNum = (raw: string, old: number) => {
	const n = Number(raw.replace(',', '.'));
	return raw.trim() === '' || !Number.isFinite(n) ? old : n;
};
