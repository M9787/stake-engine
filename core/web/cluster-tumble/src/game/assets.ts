import { slotAssets } from '../slots/slots';

// Core asset list (plan v3.3 slice 10.6b). The core ships no art: every image comes from the skin through
// the slot system (`slot:<id>` keys, src/slots), and the Howler audio sprite is generated per skin
// (tools/assets/audio.py -> build/<GAME>/web/static-gen/assets/audio). Same URL rule as src/slots/slots.ts.
export default {
	sound: {
		type: 'audio',
		src: new URL('../../assets/audio/sounds.json', import.meta.url).href,
		preload: true,
	},
	...slotAssets,
} as const;
