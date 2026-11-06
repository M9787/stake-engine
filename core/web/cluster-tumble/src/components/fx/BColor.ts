// Palette helpers for code-drawn effects (plan v3.3 slice 10.6b). Colours come from the skin theme
// (slots.ts `palette`: 0 dark base, 1 secondary, 2 accent, 3 light, 4 hot accent).
import { palette } from '../../slots/slots';

const FALLBACK = [0x14141f, 0x5b3a8a, 0xd4a845, 0xf2ead8, 0xff6a3d];

/** Palette entry i as a Pixi colour number. */
export const pal = (i: number): number => {
	const c = palette[i];
	return c && /^#[0-9a-fA-F]{6}/.test(c) ? parseInt(c.slice(1, 7), 16) : FALLBACK[i] ?? 0xffffff;
};

export const WHITE_GOLD = 0xfff4cc;

export type SigilLook = { fill: number; alpha: number; rim: number | null; atCap: boolean };

/**
 * Look of a multiplier spot by value (docs: marked = light at 40 %, x2-x8 accent, x16-x64 secondary
 * with accent rim, x128-x512 hot accent with accent rim, at the grid cap white-gold pulse).
 */
export const sigilLook = (value: number, cap: number): SigilLook => {
	if (value >= cap) return { fill: WHITE_GOLD, alpha: 1, rim: pal(2), atCap: true };
	if (value >= 128) return { fill: pal(4), alpha: 1, rim: pal(2), atCap: false };
	if (value >= 16) return { fill: pal(1), alpha: 1, rim: pal(2), atCap: false };
	if (value >= 2) return { fill: pal(2), alpha: 1, rim: null, atCap: false };
	return { fill: pal(3), alpha: 0.4, rim: null, atCap: false };
};
