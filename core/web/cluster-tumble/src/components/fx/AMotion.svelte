<script lang="ts" module>
	import type { Snippet } from 'svelte';

	export type Props = {
		/** Preset name from APresets.ts (cardIn, wipe) or src/motion/presets.ts. */
		preset: string;
		/** Changing this value restarts the motion. */
		play?: unknown;
		loop?: boolean;
		/** Reference size in px (wipe distance). Read per frame, so a resize does not restart. */
		size?: number;
		x?: number;
		y?: number;
		oncomplete?: () => void;
		children: Snippet<[{ glow: number }]>;
	};
</script>

<script lang="ts">
	// Local wrapper like src/motion/Motion.svelte, plus horizontal scale (sx) for flips.
	// Frames come from requestAnimationFrame and performance.now() (fake-clock friendly).
	import { untrack } from 'svelte';
	import { Container } from 'pixi-svelte';
	import { stateBetDerived } from 'state-shared';

	import { aPresetOf, type APose } from './APresets';

	const props: Props = $props();

	let current = $state<APose>({ dx: 0, dy: 0, scale: 1, alpha: 1, rotation: 0, glow: 0, sx: 1 });

	$effect(() => {
		props.play;
		const preset = aPresetOf(props.preset);
		const loop = props.loop ?? preset.loop ?? false;
		const speed = Math.max(0.1, stateBetDerived.timeScale?.() ?? 1);
		const duration = preset.duration / speed;
		const start = performance.now();
		let raf = 0;
		let done = false;

		current = untrack(() => preset.pose(0, props.size ?? 100));
		const frame = () => {
			const elapsed = performance.now() - start;
			const t = duration <= 0 ? 1 : loop ? (elapsed % duration) / duration : Math.min(1, elapsed / duration);
			current = preset.pose(t, props.size ?? 100);
			if (!loop && t >= 1) {
				if (!done) {
					done = true;
					props.oncomplete?.();
				}
				return;
			}
			raf = requestAnimationFrame(frame);
		};
		raf = requestAnimationFrame(frame);
		return () => cancelAnimationFrame(raf);
	});
</script>

<Container
	x={(props.x ?? 0) + current.dx}
	y={(props.y ?? 0) + current.dy}
	scale={{ x: current.scale * current.sx, y: current.scale }}
	alpha={current.alpha}
	rotation={current.rotation}
>
	{@render props.children({ glow: current.glow })}
</Container>
