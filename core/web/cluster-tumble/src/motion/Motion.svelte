<script lang="ts" module>
	import type { Snippet } from 'svelte';

	export type Props = {
		/** Preset name from presets.ts (land, pulse, dissolve, glowWin, parallax, shockwave, static). */
		preset: string | null | undefined;
		/** Changing this value restarts the motion (e.g. the symbol state). */
		play?: unknown;
		loop?: boolean;
		/** Reference size in px for presets that move (drop height, drift). */
		size?: number;
		x?: number;
		y?: number;
		zIndex?: number;
		oncomplete?: () => void;
		children: Snippet<[{ glow: number }]>;
	};
</script>

<script lang="ts">
	// Plays one motion preset on its children (plan v3.3 slice 10.6b). Frames come from
	// requestAnimationFrame and performance.now(), so Playwright's fake clock drives them in tests.
	import { Container } from 'pixi-svelte';
	import { stateBetDerived } from 'state-shared';

	import { presetOf, type Pose } from './presets';

	const props: Props = $props();

	let current = $state<Pose>({ dx: 0, dy: 0, scale: 1, alpha: 1, rotation: 0, glow: 0 });

	$effect(() => {
		props.play;
		const preset = presetOf(props.preset);
		const loop = props.loop ?? preset.loop ?? false;
		const size = props.size ?? 100;
		const speed = Math.max(0.1, stateBetDerived.timeScale?.() ?? 1);
		const duration = preset.duration / speed;
		const start = performance.now();
		let raf = 0;
		let done = false;

		const frame = () => {
			const elapsed = performance.now() - start;
			const t = duration <= 0 ? 1 : loop ? (elapsed % duration) / duration : Math.min(1, elapsed / duration);
			current = preset.pose(t, size);
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
	scale={current.scale}
	alpha={current.alpha}
	rotation={current.rotation}
	zIndex={props.zIndex}
>
	{@render props.children({ glow: current.glow })}
</Container>
