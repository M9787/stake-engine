<script lang="ts">
	// Win number in the runtime bitmap font, with a soft glow copy (FONT.winBlur) behind it.
	import { Container } from 'pixi-svelte';
	import { ResponsiveBitmapText } from 'components-pixi';

	import { FONT } from '../../slots/fonts';

	type Props = {
		text: string;
		fontSize: number;
		maxWidth: number;
		x?: number;
		y?: number;
		/** 0..1, brightens the glow copy (from a Motion preset). */
		glow?: number;
	};

	const props: Props = $props();
	const style = (fontFamily: string) => ({ fontFamily, fontSize: props.fontSize, align: 'center' as const, letterSpacing: 0 });
</script>

<Container x={props.x ?? 0} y={props.y ?? 0}>
	<Container alpha={0.35 + 0.45 * (props.glow ?? 0)}>
		<ResponsiveBitmapText anchor={0.5} maxWidth={props.maxWidth} text={props.text} style={style(FONT.winBlur)} />
	</Container>
	<ResponsiveBitmapText anchor={0.5} maxWidth={props.maxWidth} text={props.text} style={style(FONT.win)} />
</Container>
