// Client-safe desk types: the shared contract (src/lib/types.ts) plus the asset-desk additions
// returned by GET /api/game/[id]/assets (built in src/lib/server/assets.ts).
import type { AssetDesk, SlotCard } from '$lib/types';

export type DeskCard = SlotCard & {
	tool: string; // tools.v1.json id (midjourney, suno, cc0, google-fonts-ofl)
	licenceDefault: string; // the tool's usual licence, pre-selected in the picker
	drift: boolean; // provenance promptSha differs from the current prompt [P8]
};
export type Desk = Omit<AssetDesk, 'slots'> & {
	slots: DeskCard[];
	sref: string | null; // skins/<skin>/assets.json style.sref; null = hero not picked yet [P6]
	minutesLogged: Record<string, number>; // provenance.json minutes per sitting [P3]
	suno: { needed: number; have: number; limit: number | null };
	unknownFiles: string[]; // check_art_in --json unknownFiles
	checklist: string[]; // tools/assets/contact_sheet.py CHECKLIST
	contact: string[]; // contact sheets that exist: land, port, all
};
