<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	// Every image slot of the current skin (GAME), filled or on its procedural fallback (plan v3.3 10.6a).
	const { Story } = defineMeta({ title: 'Core/<SlotVisual> gallery' });
</script>

<script lang="ts">
	import { Container, Text } from 'pixi-svelte';
	import { StoryPixiApp } from 'components-storybook';

	import SlotVisual from './SlotVisual.svelte';
	import { slots } from './slots';
	import assets from '../game/assets';

	const CELL = 150;
	const COLS = 8;
	const imageSlots = Object.entries(slots).filter(([, s]) => s.kind === 'image');
	const size = (px?: readonly number[]) => {
		const [w, h] = px ?? [1, 1];
		const k = (CELL - 30) / Math.max(w, h);
		return { width: w * k, height: h * k };
	};
</script>

<Story name="all slots">
	{#snippet template()}
		<StoryPixiApp {assets}>
			<Container x={20} y={20}>
				{#each imageSlots as [id, entry], i}
					{@const s = size(entry.px)}
					<SlotVisual
						id={id}
						x={(i % COLS) * CELL + CELL / 2}
						y={Math.floor(i / COLS) * CELL + CELL / 2 - 10}
						width={s.width}
						height={s.height}
					/>
					<Text
						text={id}
						x={(i % COLS) * CELL + 4}
						y={Math.floor(i / COLS) * CELL + CELL - 22}
						style={{ fontSize: 11, fill: 0xffffff }}
					/>
				{/each}
			</Container>
		</StoryPixiApp>
	{/snippet}
</Story>
