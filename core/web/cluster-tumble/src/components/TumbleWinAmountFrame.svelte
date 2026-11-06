<script lang="ts">
	// Tumble win panel drawn in the skin palette (replaces the sample frame sprites): a rounded panel
	// with a title tab above it.
	import type { Snippet } from 'svelte';
	import type { Graphics as PixiGraphics } from 'pixi.js';

	import { BitmapText, Container, Graphics, type Sizes } from 'pixi-svelte';

	import { SYMBOL_SIZE } from '../game/constants';
	import { FONT } from '../slots/fonts';
	import { pal } from './fx/BColor';

	type Props = {
		children: Snippet<[{ frameSizes: Sizes }]>;
	};

	const props: Props = $props();
	const TITLE_RATIO = 532 / 143;
	const TITLE_HEIGHT = SYMBOL_SIZE * 0.28;
	const TITLE_SIZES = {
		width: TITLE_HEIGHT * TITLE_RATIO,
		height: TITLE_HEIGHT,
	};

	const PANEL_RATIO = 1442 / 374;
	const PANEL_HEIGHT = SYMBOL_SIZE * 0.8;
	const PANEL_SIZES = {
		width: PANEL_HEIGHT * PANEL_RATIO,
		height: PANEL_HEIGHT,
	};

	// centred rounded panel: dark base fill, accent rim, faint inner line
	const panel = (w: number, h: number, fill: number) => (g: PixiGraphics) => {
		const r = h * 0.3;
		const rim = Math.max(2, h * 0.06);
		g.roundRect(-w / 2, -h / 2, w, h, r)
			.fill({ color: fill, alpha: 0.9 })
			.stroke({ color: pal(2), width: rim });
		g.roundRect(-w / 2 + rim * 1.5, -h / 2 + rim * 1.5, w - rim * 3, h - rim * 3, r * 0.8).stroke({
			color: pal(3),
			width: rim * 0.35,
			alpha: 0.35,
		});
	};
</script>

<Graphics draw={panel(PANEL_SIZES.width, PANEL_SIZES.height, pal(0))} />

<Container y={-TITLE_HEIGHT * 1.2}>
	<Graphics draw={panel(TITLE_SIZES.width, TITLE_SIZES.height, pal(1))} />
	<BitmapText
		anchor={0.5}
		y={-TITLE_HEIGHT * 0.025}
		text="TUMBLE WIN"
		style={{ fontFamily: FONT.accent, fontSize: TITLE_HEIGHT * 0.45 }}
	/>
</Container>

{@render props.children({ frameSizes: PANEL_SIZES })}
