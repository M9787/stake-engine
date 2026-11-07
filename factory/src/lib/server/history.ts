// Skin history (plan v3.3 M12): every editor write first copies the editable skin files to
// skins/<skin>/.history/<YYYYMMDD-HHMMSS>/. Restore snapshots the current state first, then copies back.
// Only game.json, text/*, assets.json and math/reels/* are covered (the files the editor or new_game.py write).
import fs from 'node:fs';
import path from 'node:path';

import { inside } from './repo';

const KEEP = 50;
const TS = /^\d{8}-\d{6}(-\d{1,2})?$/;
const FILES = ['game.json', 'assets.json'];
const DIRS = [['text'], ['math', 'reels']];

export type Snapshot = { ts: string; files: string[] };

const histDir = (skinDir: string) => path.join(skinDir, '.history');
const pad = (n: number) => String(n).padStart(2, '0');
const stamp = (d = new Date()) =>
	`${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;

/** Relative paths (forward slashes) of the covered files that exist under `base`. */
const covered = (base: string): string[] => {
	const out: string[] = [];
	for (const f of FILES) if (fs.existsSync(path.join(base, f))) out.push(f);
	for (const parts of DIRS) {
		const d = path.join(base, ...parts);
		if (!fs.existsSync(d)) continue;
		for (const e of fs.readdirSync(d, { withFileTypes: true })) if (e.isFile()) out.push([...parts, e.name].join('/'));
	}
	return out.sort();
};

const copy = (fromBase: string, toBase: string, rel: string) => {
	const dst = inside(toBase, ...rel.split('/'));
	fs.mkdirSync(path.dirname(dst), { recursive: true });
	fs.copyFileSync(inside(fromBase, ...rel.split('/')), dst);
};

/** Copy the covered files of a skin into a new snapshot folder; returns its timestamp id. */
export const snapshot = (skinDir: string): string => {
	const h = histDir(skinDir);
	fs.mkdirSync(h, { recursive: true });
	let ts = stamp();
	for (let i = 2; fs.existsSync(path.join(h, ts)); i++) ts = `${stamp()}-${i}`;
	const dir = path.join(h, ts);
	fs.mkdirSync(dir);
	for (const rel of covered(skinDir)) copy(skinDir, dir, rel);
	prune(skinDir);
	return ts;
};

/** Snapshots, newest first. */
export const list = (skinDir: string): Snapshot[] => {
	const h = histDir(skinDir);
	if (!fs.existsSync(h)) return [];
	return fs
		.readdirSync(h, { withFileTypes: true })
		.filter((e) => e.isDirectory() && TS.test(e.name))
		.map((e) => ({ ts: e.name, files: covered(path.join(h, e.name)) }))
		.sort((a, b) => b.ts.localeCompare(a.ts, 'en', { numeric: true }));
};

const prune = (skinDir: string) => {
	for (const old of list(skinDir).slice(KEEP)) fs.rmSync(path.join(histDir(skinDir), old.ts), { recursive: true, force: true });
};

/** Restore snapshot `ts`: snapshot the current state first, then make the covered files equal to the snapshot
 *  (covered files that did not exist at snapshot time are removed; they stay in the new safety snapshot). */
export const restore = (skinDir: string, ts: string): { restored: string; backup: string } => {
	if (!TS.test(ts)) throw new Error(`invalid snapshot id '${ts}'`);
	const src = path.join(histDir(skinDir), ts);
	if (!fs.existsSync(src)) throw new Error(`unknown snapshot '${ts}'`);
	const want = covered(src);
	if (!want.includes('game.json')) throw new Error(`snapshot '${ts}' has no game.json`);
	// Read first: the safety snapshot may prune the oldest snapshot, which can be this one.
	const data = new Map(want.map((rel) => [rel, fs.readFileSync(inside(src, ...rel.split('/')))]));
	const backup = snapshot(skinDir);
	for (const rel of covered(skinDir)) if (!data.has(rel)) fs.rmSync(inside(skinDir, ...rel.split('/')));
	for (const [rel, buf] of data) {
		const dst = inside(skinDir, ...rel.split('/'));
		fs.mkdirSync(path.dirname(dst), { recursive: true });
		fs.writeFileSync(dst, buf);
	}
	return { restored: ts, backup };
};
