// Procedural fallbacks for empty image slots (docs/10 plan v3.3 section 3). Drawn with Pixi Graphics in the
// skin's palette, so a skin with no art still shows a coherent, readable game. Never shipped: package.ps1
// refuses a required slot that is still on its fallback.
import type * as PIXI from 'pixi.js';

const hex = (c: string | undefined, fallback: number) =>
	c && /^#[0-9a-fA-F]{6}/.test(c) ? parseInt(c.slice(1, 7), 16) : fallback;

/** Deterministic small hash so each symbol id gets its own shape and colour. */
const hash = (s: string) => [...s].reduce((h, ch) => (h * 31 + ch.charCodeAt(0)) >>> 0, 7);

export type Recipe = (g: PIXI.Graphics, w: number, h: number, palette: string[], id: string, tier?: string) => void;

const gem: Recipe = (g, w, h, palette, id, tier) => {
	const n = hash(id);
	// Only colours bright enough to read on the dark board backdrop.
	const luminance = (c: string) => {
		const v = hex(c, 0);
		return (0.299 * ((v >> 16) & 255) + 0.587 * ((v >> 8) & 255) + 0.114 * (v & 255)) / 255;
	};
	const bright = palette.filter((c) => luminance(c) > 0.22);
	const colours = bright.length ? bright : ['#8888cc', '#c0a050'];
	const fill = hex(colours[n % colours.length], 0x8888cc);
	const rim = hex(colours[0], 0x222233);
	const r = Math.min(w, h) * (tier === 'high' ? 0.46 : 0.4);
	const sides = tier === 'high' ? 6 + (n % 3) : 4 + (n % 2);
	const pts: number[] = [];
	for (let i = 0; i < sides; i++) {
		const a = -Math.PI / 2 + (i * 2 * Math.PI) / sides;
		pts.push(w / 2 + Math.cos(a) * r, h / 2 + Math.sin(a) * r);
	}
	g.poly(pts).fill({ color: fill }).stroke({ color: rim, width: Math.max(2, r * 0.08) });
	g.circle(w / 2, h / 2, r * 0.35).fill({ color: 0xffffff, alpha: tier === 'high' ? 0.35 : 0.2 });
};

const orb: Recipe = (g, w, h, palette) => {
	const r = Math.min(w, h) * 0.44;
	g.circle(w / 2, h / 2, r).fill({ color: hex(palette[1], 0x6633aa) }).stroke({ color: hex(palette[2], 0xd4a845), width: r * 0.1 });
	g.circle(w / 2 - r * 0.3, h / 2 - r * 0.3, r * 0.25).fill({ color: 0xffffff, alpha: 0.5 });
};

const ring: Recipe = (g, w, h, palette) => {
	const r = Math.min(w, h) * 0.42;
	g.circle(w / 2, h / 2, r).stroke({ color: hex(palette[2], 0xd4a845), width: r * 0.18 });
};

const gradient: Recipe = (g, w, h, palette) => {
	const top = hex(palette[0], 0x10101a);
	const bottom = hex(palette[palette.length - 1], 0x000000);
	const bands = 24;
	for (let i = 0; i < bands; i++) {
		const t = i / (bands - 1);
		const mix = (a: number, b: number, s: number) => Math.round(a + (b - a) * t) << s;
		const c =
			mix((top >> 16) & 255, (bottom >> 16) & 255, 16) |
			mix((top >> 8) & 255, (bottom >> 8) & 255, 8) |
			mix(top & 255, bottom & 255, 0);
		g.rect(0, (h * i) / bands, w, h / bands + 1).fill({ color: c });
	}
};

const frame: Recipe = (g, w, h, palette) => {
	const t = Math.min(w, h) * 0.03;
	g.roundRect(t / 2, t / 2, w - t, h - t, t * 2).stroke({ color: hex(palette[2], 0xd4a845), width: t });
};

const panel: Recipe = (g, w, h, palette) => {
	g.roundRect(0, 0, w, h, Math.min(w, h) * 0.08)
		.fill({ color: hex(palette[0], 0x14141f), alpha: 0.92 })
		.stroke({ color: hex(palette[2], 0xd4a845), width: Math.min(w, h) * 0.03 });
};

const fade: Recipe = (g, w, h, palette) => {
	g.rect(0, 0, w, h).fill({ color: hex(palette[1], 0x333355), alpha: 0.85 });
};

const emblem: Recipe = (g, w, h, palette) => {
	ring(g, w, h, palette, '');
	g.circle(w / 2, h / 2, Math.min(w, h) * 0.22).fill({ color: hex(palette[1], 0x6633aa) });
};

export const RECIPES: Record<string, Recipe> = {
	tierGem: gem,
	scatterOrb: orb,
	ring,
	gradient,
	frame,
	banner: panel,
	card: panel,
	fade,
	emblem,
};

/** Draw `procedural:<recipe>` (unknown recipes draw a neutral panel). */
export const drawFallback = (
	g: PIXI.Graphics,
	fallback: string | null,
	w: number,
	h: number,
	palette: string[],
	id: string,
	tier?: string,
) => {
	const name = (fallback ?? '').replace('procedural:', '');
	(RECIPES[name] ?? panel)(g, w, h, palette, id, tier);
};
