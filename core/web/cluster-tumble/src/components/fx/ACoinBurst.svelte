<script lang="ts">
	// Coin fountain drawn in code (no coin sprites): palette-accent discs that spin, fly up and fall.
	// Frames come from requestAnimationFrame and performance.now() (fake-clock friendly).
	import { Graphics } from 'pixi-svelte';
	import type * as PIXI from 'pixi.js';

	import { palette } from '../../slots/slots';

	type Props = {
		emit?: boolean;
		/** Coins per second while emitting. */
		rate: number;
		/** Reference size in px (board width): sets speed, gravity and coin size. */
		size: number;
	};

	type Coin = { x: number; y: number; vx: number; vy: number; r: number; spin: number; spinV: number; life: number };

	const props: Props = $props();
	const accent = palette[2] ?? '#D4A845';
	const rim = palette[0] ?? '#000000';
	const MAX_COINS = 160;

	const coins: Coin[] = [];
	let frame = $state(0);

	const spawn = (size: number) => {
		if (coins.length >= MAX_COINS) return;
		coins.push({
			x: (Math.random() - 0.5) * size * 0.4,
			y: size * 0.15,
			vx: (Math.random() - 0.5) * size * 1.6,
			vy: -size * (1.5 + Math.random() * 0.9),
			r: size * (0.022 + Math.random() * 0.014),
			spin: Math.random() * Math.PI,
			spinV: 6 + Math.random() * 8,
			life: 2.6,
		});
	};

	$effect(() => {
		let raf = 0;
		let last = performance.now();
		let carry = 0;
		const tick = () => {
			const now = performance.now();
			const dt = Math.min(0.05, (now - last) / 1000);
			last = now;
			const size = props.size;
			if (props.emit) {
				carry += props.rate * dt;
				for (; carry >= 1; carry--) spawn(size);
			}
			for (const c of coins) {
				c.vy += size * 2.6 * dt;
				c.x += c.vx * dt;
				c.y += c.vy * dt;
				c.spin += c.spinV * dt;
				c.life -= dt;
			}
			for (let i = coins.length - 1; i >= 0; i--) if (coins[i].life <= 0) coins.splice(i, 1);
			frame++;
			raf = requestAnimationFrame(tick);
		};
		raf = requestAnimationFrame(tick);
		return () => cancelAnimationFrame(raf);
	});

	const draw = (g: PIXI.Graphics) => {
		for (const c of coins) {
			// |cos| squashes the disc horizontally: reads as a coin spinning on its axis.
			const rx = Math.max(c.r * 0.12, c.r * Math.abs(Math.cos(c.spin)));
			const alpha = Math.min(1, c.life * 2);
			g.ellipse(c.x, c.y, rx, c.r).fill({ color: accent, alpha }).stroke({ color: rim, width: c.r * 0.18, alpha });
			g.ellipse(c.x - rx * 0.25, c.y - c.r * 0.25, rx * 0.35, c.r * 0.35).fill({ color: '#ffffff', alpha: alpha * 0.35 });
		}
	};
</script>

<Graphics
	draw={(g) => {
		frame; // redraw every animation frame
		draw(g);
	}}
/>
