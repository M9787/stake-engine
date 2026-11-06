// @ts-ignore
import config from 'config-svelte';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Skin data (docs/10 section 1, plan v3.3): generated per game into stake\build\<GAME>\web by
// tools\gen\* (scripts\sync.ps1), imported as $skin/... Static files (images, audio, fonts, favicon)
// are served from build\<GAME>\web\static (tools\gen\gen_web_static.py). GAME has a local-dev default below.
// The app sits at <stake>\core\web\<app> or <stake>\web-sdk\apps\<app>: three levels below stake.
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
export const skinDir = path.join(repoRoot, 'build', process.env.GAME || 'seventh_veil', 'web'); // lint-core: allow (default game for local dev)
export const skinStatic = path.join(skinDir, 'static');

const base = config();
export default {
	...base,
	kit: {
		...base.kit,
		alias: { ...(base.kit?.alias ?? {}), $skin: skinDir },
		files: { ...(base.kit?.files ?? {}), assets: skinStatic },
	},
};
