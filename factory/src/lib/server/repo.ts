// Repo paths and skin lookup for the factory editor (server only).
import fs from 'node:fs';
import path from 'node:path';

export const ROOT = path.resolve(process.cwd(), '..'); // factory/ is one level below stake/
export const PY = path.join(ROOT, 'math-sdk', 'env', 'Scripts', 'python.exe'); // stdlib tools, math
export const PY_ASSETS = path.join(ROOT, '.venv-assets', 'Scripts', 'python.exe'); // Pillow/rembg/ffmpeg tools
export const FROZEN_GAMES = new Set(['seventh_veil']); // PROJECT.md section 4: Oracle modes and math are frozen

const GAME_ID = /^[a-z][a-z0-9_]{2,31}$/;
const SLOT_ID = /^[a-z][A-Za-z0-9]*(\.[A-Za-z0-9]+){0,3}$/;

export const readJson = <T = any>(p: string): T => JSON.parse(fs.readFileSync(p, 'utf-8'));
export const writeJson = (p: string, data: unknown) =>
	fs.writeFileSync(p, JSON.stringify(data, null, 2) + '\n', { encoding: 'utf-8' });

export type SkinRef = { id: string; skin: string; dir: string; gdef: any };

/** Every skin: skins/<skin>/game.json. */
export const listSkins = (): SkinRef[] => {
	const dir = path.join(ROOT, 'skins');
	return fs
		.readdirSync(dir, { withFileTypes: true })
		.filter((d) => d.isDirectory() && fs.existsSync(path.join(dir, d.name, 'game.json')))
		.map((d) => {
			const gdef = readJson(path.join(dir, d.name, 'game.json'));
			return { id: gdef.identity.gameId, skin: d.name, dir: path.join(dir, d.name), gdef };
		})
		.sort((a, b) => a.id.localeCompare(b.id));
};

/** The skin of a game id, or throws 404-style Error. Validates the id format first. */
export const skinOf = (id: string): SkinRef => {
	if (!GAME_ID.test(id)) throw new Error(`invalid game id '${id}'`);
	const s = listSkins().find((x) => x.id === id);
	if (!s) throw new Error(`unknown game '${id}'`);
	return s;
};

export const isGameId = (id: string) => GAME_ID.test(id);
export const isSlotId = (id: string) => SLOT_ID.test(id);

/** Resolve a path and make sure it stays inside `base` (no traversal). */
export const inside = (base: string, ...parts: string[]) => {
	const p = path.resolve(base, ...parts);
	const b = path.resolve(base) + path.sep;
	if (!(p + path.sep).startsWith(b) && p !== path.resolve(base)) throw new Error('path outside allowed folder');
	return p;
};

export const buildDir = (id: string) => path.join(ROOT, 'build', id);
export const libraryDir = (id: string) => path.join(ROOT, 'math-sdk', 'games', id, 'library');
