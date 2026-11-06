<script lang="ts" module>
	import { sound, type MusicName, type SoundEffectName, type SoundName } from '../game/sound';

	export type EmitterEventSound =
		| { type: 'soundMusic'; name: MusicName }
		| { type: 'soundOnce'; name: SoundEffectName; forcePlay?: boolean }
		| { type: 'soundLoop'; name: SoundEffectName }
		| { type: 'soundStop'; name: SoundName }
		| { type: 'soundFade'; name: SoundName; from: number; to: number; duration: number }
		| { type: 'soundScatterCounterIncrease' }
		| { type: 'soundScatterCounterClear' };
</script>

<script lang="ts">
	import { onMount } from 'svelte';

	import { waitForTimeout } from 'utils-shared/wait';
	import { SECOND } from 'constants-shared/time';
	import { stateBet } from 'state-shared';

	import skin from '$skin/skin.generated';
	import { getContext } from '../game/context';

	const context = getContext();

	// Music per mode comes from the skin (game.json presentation.modes, default: 'feature' for spin
	// modes priced above 1x). Unknown keys fall back to the main theme.
	const modeMusic: Record<string, string> = skin.modeMusic;
	const musicFor = (betModeKey: string): MusicName => (modeMusic[betModeKey] ?? 'bgm_main') as MusicName;

	context.eventEmitter.subscribeOnMount({
		// ui
		soundBetMode: async ({ betModeKey }) => {
			const music = musicFor(betModeKey);
			if (music !== 'bgm_main') {
				sound.players.once.play({ name: 'sfx_winlevel_end' });
				await waitForTimeout(SECOND);
			}
			sound.players.music.play({ name: music });
		},
		soundPressGeneral: () => sound.players.once.play({ name: 'sfx_btn_general' }),
		soundPressBet: () => sound.players.once.play({ name: 'sfx_btn_spin' }),
		// scatterCounter
		soundScatterCounterIncrease: () => (context.stateGame.scatterCounter = context.stateGame.scatterCounter + 1), // prettier-ignore
		soundScatterCounterClear: () => (context.stateGame.scatterCounter = 0),
		// game
		soundMusic: ({ name }) => sound.players.music.play({ name }),
		soundLoop: ({ name }) => sound.players.loop.play({ name }),
		soundOnce: ({ name, forcePlay }) => sound.players.once.play({ name, forcePlay }),
		soundStop: ({ name }) => sound.stop({ name }),
		soundFade: async ({ name, duration, from, to }) => await sound.fade({ name, duration, from, to }), // prettier-ignore
	});

	onMount(() => {
		sound.players.music.play({ name: musicFor(stateBet.activeBetModeKey) });
	});
</script>
