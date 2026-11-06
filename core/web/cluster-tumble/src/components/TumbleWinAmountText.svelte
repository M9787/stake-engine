<script lang="ts">
	// Tumble win number in FONT.accent. Plain update: count up, then oncomplete (as before).
	// animate: a 'shockwave' pop replaces the sample Spine 'explosion'; the number updates at the start
	// of the pop and oncomplete fires when the pop ends.
	import { Tween } from 'svelte/motion';

	import { ResponsiveBitmapText } from 'components-pixi';
	import { bookEventAmountToCurrencyString } from 'utils-shared/amount';

	import { SYMBOL_SIZE } from '../game/constants';
	import Motion from '../motion/Motion.svelte';
	import { FONT } from '../slots/fonts';

	type Props = {
		width: number;
		amount: number;
		animate: boolean;
		oncomplete: () => void;
	};

	type AnimationName = 'idle' | 'explosion';

	const props: Props = $props();
	const amount = new Tween(0);
	const animationName = $derived<AnimationName>(props.animate ? 'explosion' : 'idle');

	const normalUpdate = async () => {
		await amount.set(props.amount);
		props.oncomplete();
	};

	$effect(() => {
		if (animationName === 'idle') normalUpdate();
		else amount.set(props.amount);
	});
</script>

<Motion
	preset={animationName === 'explosion' ? 'shockwave' : 'pulse'}
	play={props.amount}
	oncomplete={() => {
		if (animationName === 'explosion') props.oncomplete();
	}}
>
	{#snippet children()}
		<ResponsiveBitmapText
			anchor={0.5}
			style={{
				fontFamily: FONT.accent,
				fontSize: 0.65 * SYMBOL_SIZE,
			}}
			text={bookEventAmountToCurrencyString(amount.current)}
			maxWidth={props.width}
		/>
	{/snippet}
</Motion>
