// Motion presets (docs/10 plan v3.3, slice 10.6b): code-driven movement for flat images, so a skin
// needs no Spine rigs. A preset maps progress t (0..1) to a pose. Durations are in ms at normal speed;
// the Motion component divides by the bet time scale (turbo).

export type Pose = { dx: number; dy: number; scale: number; alpha: number; rotation: number; glow: number };
export type Preset = { duration: number; loop?: boolean; pose: (t: number, size: number) => Pose };

const REST: Pose = { dx: 0, dy: 0, scale: 1, alpha: 1, rotation: 0, glow: 0 };
const pose = (p: Partial<Pose>): Pose => ({ ...REST, ...p });

const easeOutBack = (t: number) => {
	const c1 = 1.70158;
	const c3 = c1 + 1;
	return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
};
const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
const bump = (t: number) => Math.sin(Math.PI * t); // 0 -> 1 -> 0

export const PRESETS: Record<string, Preset> = {
	/** No movement; completes on the next frame. */
	static: { duration: 0, pose: () => REST },
	/** Symbol lands: small drop with an overshoot. */
	land: {
		duration: 260,
		pose: (t, size) => {
			const e = easeOutBack(t);
			return pose({ dy: (1 - e) * -0.18 * size, scale: 0.92 + 0.08 * e });
		},
	},
	/** Winning symbol: two heart-beats with a glow. */
	pulse: {
		duration: 900,
		pose: (t) => {
			const beat = bump((t * 2) % 1);
			return pose({ scale: 1 + 0.16 * beat, glow: beat });
		},
	},
	/** Removed symbol: swells and fades. */
	dissolve: {
		duration: 340,
		pose: (t) => {
			const e = easeOutCubic(t);
			return pose({ scale: 1 + 0.35 * e, alpha: 1 - e, glow: 1 - e });
		},
	},
	/** Board frame / panel highlight: slow breathing glow (loops). */
	glowWin: { duration: 1600, loop: true, pose: (t) => pose({ glow: 0.4 + 0.6 * bump(t) }) },
	/** Background: very slow drift (loops). */
	parallax: {
		duration: 24000,
		loop: true,
		pose: (t, size) => {
			const a = t * Math.PI * 2;
			return pose({ dx: Math.sin(a) * 0.006 * size, dy: Math.cos(a) * 0.004 * size, scale: 1.02 });
		},
	},
	/** Big moment: punch-in scale with a flash. */
	shockwave: {
		duration: 700,
		pose: (t) => {
			const e = easeOutBack(Math.min(1, t * 1.6));
			return pose({ scale: 0.6 + 0.4 * e, glow: 1 - t });
		},
	},
};

export const presetOf = (name: string | null | undefined): Preset => PRESETS[name ?? 'static'] ?? PRESETS.static;
