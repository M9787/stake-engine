// Font roles (plan v3.3 slice 10.6b). The core never ships a skin font: the skin fills slots font.display /
// font.ui (OFL TTF, see core/assets/slots.v1.json); until then the bundled UI font is used.
// Bitmap fonts for win numbers are generated at runtime from the display font and the skin theme, so no
// .xml/.png bitmap font files exist anywhere.
import { BitmapFont } from 'pixi.js';
import skin from '$skin/skin.generated';

import { slotFonts } from './slots';

/** Bitmap font names the components use (BitmapText fontFamily). */
export const FONT = {
	win: 'ct-win', // big win numbers
	winBlur: 'ct-win-blur', // soft glow copy behind win numbers
	accent: 'ct-accent', // tumble win, multipliers
	counter: 'ct-counter', // free spin counter
} as const;

/** CSS family for HTML/Pixi Text: the skin's UI font when filled, else the core UI font. */
export const UI_FONT = slotFonts['font-ui'] ? 'font-ui' : 'proxima-nova';
const DISPLAY_FONT = slotFonts['font-display'] ? 'font-display' : 'proxima-nova';

const CHARS = [['0', '9'], ['A', 'Z'], ['a', 'z'], ' .,:;!?+-×x%$€£¥₹₩₱₽₺₫()/'];

const theme = skin.theme as Record<string, any>;
const gradient: string[] = theme.fontGradient ?? ['#ffffff', '#dddddd', '#aaaaaa'];
const stroke: string = theme.fontStroke ?? '#000000';

let installed: Promise<void> | null = null;

/** Register the skin's TTFs with the browser, then build the bitmap fonts. Idempotent. */
export const installFonts = () => {
	installed ??= (async () => {
		for (const [family, url] of Object.entries(slotFonts)) {
			try {
				const face = new FontFace(family, `url(${url})`);
				await face.load();
				document.fonts.add(face);
			} catch (err) {
				console.error(`font slot ${family} failed to load`, err);
			}
		}
		const base = { fontFamily: DISPLAY_FONT, fontWeight: 'bold' as const };
		BitmapFont.install({
			name: FONT.win,
			style: { ...base, fontSize: 96, fill: gradient[1] ?? gradient[0], stroke: { color: stroke, width: 6 } },
			chars: CHARS,
			resolution: 2,
		});
		BitmapFont.install({
			name: FONT.winBlur,
			style: { ...base, fontSize: 96, fill: gradient[0], stroke: { color: gradient[0], width: 14 } },
			chars: CHARS,
			resolution: 1,
		});
		BitmapFont.install({
			name: FONT.accent,
			style: { ...base, fontSize: 64, fill: gradient[0], stroke: { color: stroke, width: 5 } },
			chars: CHARS,
			resolution: 2,
		});
		BitmapFont.install({
			name: FONT.counter,
			style: { ...base, fontSize: 56, fill: '#ffffff', stroke: { color: stroke, width: 5 } },
			chars: CHARS,
			resolution: 2,
		});
	})();
	return installed;
};
