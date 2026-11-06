<script lang="ts">
	// "Press anywhere" prompt: UI-font text with a looping pulse; Space or any press calls onpress.
	import { MainContainer, OnPressFullScreen } from 'components-layout';
	import { OnHotkey } from 'components-shared';
	import { Text } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { t } from '../game/wording';
	import Motion from '../motion/Motion.svelte';
	import { labelStyle } from './fx/AText';

	type Props = {
		onpress: () => void;
	};

	const props: Props = $props();
	const context = getContext();
</script>

<MainContainer alignVertical="bottom">
	<Motion
		preset="pulse"
		loop
		x={context.stateLayoutDerived.mainLayout().width * 0.5}
		y={context.stateLayoutDerived.mainLayout().height - 80}
	>
		{#snippet children()}
			<Text anchor={0.5} text={t('PRESS ANYWHERE TO CONTINUE')} style={labelStyle(40, '#ffffff')} />
		{/snippet}
	</Motion>
</MainContainer>
<OnHotkey hotkey="Space" onpress={() => props.onpress()} />
<OnPressFullScreen onpress={() => props.onpress()} />
