// Asset slots of the current skin (docs/10 plan v3.3 section 3, slice 10.6a).
// $skin/assets.generated (tools/gen/gen_assets_ts.py) says which slots the skin has filled. Filled image
// slots load as Pixi sprites under the key `slot:<id>`; empty ones render their procedural fallback
// (procedural.ts), so a skin always runs, even with no art at all.
import skinAssets from '$skin/assets.generated';

export type SlotEntry = {
	kind: 'image' | 'font';
	file: string | null;
	fallback: string | null;
	motion: string | null;
	px?: readonly number[];
	tier?: string;
};

export const slots = skinAssets.slots as unknown as Record<string, SlotEntry>;
export const palette: string[] = [...skinAssets.palette];

// Same resolution rule as the core assets.ts: '../../' from src/<dir>/ is the static root in dev, and
// in the build Vite rewrites import.meta.url to the bundle script in _app/immutable/, two levels down.
// String concatenation on purpose: a template literal would trigger Vite's glob import transform.
const staticUrl = (file: string) => new URL('../../' + file, import.meta.url).href;

export const slotKey = (id: string) => 'slot:' + id;
export const isFilled = (id: string) => Boolean(slots[id]?.file);

/** Pixi asset entries for every filled image slot, merged into the app's assets (assets.ts). */
export const slotAssets = Object.fromEntries(
	Object.entries(slots)
		.filter(([, s]) => s.kind === 'image' && s.file)
		.map(([id, s]) => [slotKey(id), { type: 'sprite' as const, src: staticUrl(s.file as string) }]),
);

/** Font slots that the skin filled: family name -> URL (registered with FontFace at startup). */
export const slotFonts = Object.fromEntries(
	Object.entries(slots)
		.filter(([, s]) => s.kind === 'font' && s.file)
		.map(([id, s]) => [id.replace('.', '-'), staticUrl(s.file as string)]),
);
