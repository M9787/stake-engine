// @ts-ignore
import config from 'config-svelte';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Skin data (docs/10 section 1): generated per game into stake\build\<GAME>\web by
// tools\gen\gen_rules.py + gen_skin_ts.py, imported as $skin/... GAME defaults to seventh_veil.
// The app sits at <stake>\game\web\<app> or <stake>\web-sdk\apps\<app>: three levels below stake.
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
export const skinDir = path.join(repoRoot, 'build', process.env.GAME || 'seventh_veil', 'web');

const base = config();
export default {
	...base,
	kit: { ...base.kit, alias: { ...(base.kit?.alias ?? {}), $skin: skinDir } },
};
