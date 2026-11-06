// Extra motion presets for the win / bonus / transition screens (slice 10.6b). Same shape as
// src/motion/presets.ts plus `sx`, a horizontal scale factor for card flips. Base presets are reused.
import { PRESETS, type Pose } from '../../motion/presets';

export type APose = Pose & { sx: number };
export type APreset = { duration: number; loop?: boolean; pose: (t: number, size: number) => APose };

const REST: APose = { dx: 0, dy: 0, scale: 1, alpha: 1, rotation: 0, glow: 0, sx: 1 };
const pose = (p: Partial<APose>): APose => ({ ...REST, ...p });

const easeOutBack = (t: number) => 1 + 2.70158 * Math.pow(t - 1, 3) + 1.70158 * Math.pow(t - 1, 2);
const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export const A_PRESETS: Record<string, APreset> = {
	/** Bonus card: flips in edge-on, grows and settles with an overshoot. */
	cardIn: {
		duration: 650,
		pose: (t) =>
			pose({
				sx: Math.max(0.02, easeOutBack(t)),
				scale: 0.8 + 0.2 * easeOutCubic(t),
				alpha: Math.min(1, t * 3),
				glow: 1 - t,
			}),
	},
	/** Screen wipe: slides in from the right, holds while covering, slides out to the left. */
	wipe: {
		duration: 1300,
		pose: (t, size) => {
			const cover = t < 0.4 ? easeInOut(t / 0.4) : 1;
			const leave = t > 0.6 ? easeInOut((t - 0.6) / 0.4) : 0;
			return pose({ dx: size * (1 - cover) - size * leave, glow: cover - leave });
		},
	},
};

/** A_PRESETS first, then the shared presets, else static. */
export const aPresetOf = (name: string | null | undefined): APreset => {
	const own = A_PRESETS[name ?? ''];
	if (own) return own;
	const base = PRESETS[name ?? 'static'] ?? PRESETS.static;
	return { duration: base.duration, loop: base.loop, pose: (t, size) => ({ ...base.pose(t, size), sx: 1 }) };
};
