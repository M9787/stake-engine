// Game list, definition read/write and validation (plan v3.3 M12). Validation is always validate.py --json
// (one code path); this file only reads/writes the editable fields and never re-implements checks.
import { execFile } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { promisify } from 'node:util';

import type { Definition, GameSummary, ReleaseMode, ValidateResult } from '$lib/types';
import { FROZEN_GAMES, PY, ROOT, buildDir, libraryDir, listSkins, readJson, type SkinRef } from './repo';
import { snapshot } from './history';

const run = promisify(execFile);
const CATALOGUE = path.join(ROOT, 'core', 'assets', 'slots.v1.json');

// ---- format-preserving JSON edits ----------------------------------------------------------------
// Skin files are partly hand-formatted (Oracle game.json) and written by Python (5.0 stays a float). A full
// JSON.parse/stringify would reformat them and turn 5.0 into 5. Instead only the changed values are spliced into
// the original text; every other byte stays as it was.
type Path = (string | number)[];
const spans = (text: string): Map<string, [number, number]> => {
	const out = new Map<string, [number, number]>();
	let i = 0;
	const ws = () => {
		while (/\s/.test(text[i] ?? '')) i++;
	};
	const str = () => {
		const s0 = i++;
		while (text[i] !== '"') i += text[i] === '\\' ? 2 : 1;
		i++;
		return JSON.parse(text.slice(s0, i)) as string;
	};
	const value = (p: Path) => {
		ws();
		const s0 = i;
		if (text[i] === '{') {
			i++;
			ws();
			while (text[i] !== '}') {
				const k = str();
				ws();
				i++; // ':'
				value([...p, k]);
				ws();
				if (text[i] === ',') i++;
				ws();
			}
			i++;
		} else if (text[i] === '[') {
			i++;
			ws();
			for (let n = 0; text[i] !== ']'; n++) {
				value([...p, n]);
				ws();
				if (text[i] === ',') i++;
				ws();
			}
			i++;
		} else if (text[i] === '"') str();
		else {
			const m = /-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/y;
			m.lastIndex = i;
			if (!m.exec(text)) throw new Error(`bad JSON at ${i}`);
			i = m.lastIndex;
		}
		out.set(JSON.stringify(p), [s0, i]);
	};
	value([]);
	return out;
};
const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const sameKeys = (a: object, b: object) => JSON.stringify(Object.keys(a).sort()) === JSON.stringify(Object.keys(b).sort());
/** Smallest set of (path, new value) replacements; numbers of equal value count as unchanged (5 == 5.0). */
const diff = (a: unknown, b: unknown, p: Path, out: { p: Path; v: unknown }[]) => {
	if (isObj(a) && isObj(b) && sameKeys(a, b)) for (const k of Object.keys(b)) diff(a[k], b[k], [...p, k], out);
	else if (Array.isArray(a) && Array.isArray(b) && a.length === b.length) b.forEach((x, n) => diff(a[n], x, [...p, n], out));
	else if (!(a === b || (typeof a === 'object' && JSON.stringify(a) === JSON.stringify(b)))) out.push({ p, v: b });
};
/** Return `text` with the values at the given paths replaced (the paths must exist in `text`). */
export const editJson = (text: string, edits: { p: Path; v: unknown }[]): string => {
	const sp = spans(text);
	const reps = edits.map(({ p, v }) => {
		const at = sp.get(JSON.stringify(p));
		if (!at) throw new Error(`path ${p.join('.')} not found`);
		const lineStart = text.lastIndexOf('\n', at[0]) + 1;
		const indent = /^[ \t]*/.exec(text.slice(lineStart))![0];
		return { at, s: JSON.stringify(v, null, 2).replace(/\n/g, '\n' + indent) };
	});
	for (const { at, s } of reps.sort((x, y) => y.at[0] - x.at[0])) text = text.slice(0, at[0]) + s + text.slice(at[1]);
	return text;
};
/** Change `text` so it parses to `next` where it differs from what it parses to now. */
const rewrite = (text: string, next: unknown) => {
	const edits: { p: Path; v: unknown }[] = [];
	diff(JSON.parse(text), next, [], edits);
	if (edits.some((e) => e.p.length === 0)) throw new Error('this file lacks a section the editor writes (e.g. theme); add it by hand first');
	return edits.length ? editJson(text, edits) : text;
};

/** game.json release.mode; missing or unknown = 'release' (same rule as tools/gamedef/mode.py). */
export const releaseMode = (gdef: any): ReleaseMode => (gdef?.release?.mode === 'test' ? 'test' : 'release');

/** Append a new top-level key at the end of the root object of `text` (other bytes unchanged). */
const appendKey = (text: string, key: string, value: unknown): string => {
	const end = text.lastIndexOf('}');
	const body = `  ${JSON.stringify(key)}: ${JSON.stringify(value, null, 2).replace(/\n/g, '\n  ')}`;
	return text.slice(0, end).replace(/\s*$/, '') + ',\n' + body + '\n' + text.slice(end);
};

// ---- summaries ------------------------------------------------------------------------------------
const requiredIds = (s: SkinRef): string[] => {
	const prompts = path.join(buildDir(s.id), 'prompts.json');
	if (fs.existsSync(prompts)) {
		try {
			return readJson(prompts).slots.filter((x: any) => x.required === 'ship').map((x: any) => x.id);
		} catch {
			/* fall through to the catalogue */
		}
	}
	// Same expansion as tools/assets/catalog.py Catalog._expand (ids only).
	const g = s.gdef;
	const variants = g.features?.bonusVariants ?? g.bonusVariants ?? [];
	const items = (expand: string): Record<string, string>[] => {
		if (expand === 'symbols:pay') return g.symbols.filter((x: any) => x.role === 'pay').map((x: any) => ({ 'symbol.id': x.id }));
		if (expand === 'symbols:scatter') return g.symbols.filter((x: any) => x.role === 'scatter').map((x: any) => ({ 'symbol.id': x.id }));
		if (expand === 'variants') return variants.map((v: any) => ({ 'variant.id': v.id }));
		throw new Error(`unknown expand '${expand}' in slots.v1.json`);
	};
	const out: string[] = [];
	for (const raw of readJson(CATALOGUE).slots) {
		if (raw.required !== 'ship') continue;
		for (const ctx of raw.expand ? items(raw.expand) : [{}]) out.push(raw.id.replace(/\{([\w.]+)\}/g, (m: string, k: string) => ctx[k] ?? m));
	}
	return out;
};

const summary = (s: SkinRef): GameSummary => {
	const lockPath = path.join(s.dir, 'assets.lock.json');
	const lock = fs.existsSync(lockPath) ? (readJson(lockPath).slots ?? {}) : {};
	const req = requiredIds(s);
	return {
		id: s.id,
		skin: s.skin,
		displayName: s.gdef.identity.displayName,
		version: s.gdef.identity.version,
		board: { reels: s.gdef.board.reels, rows: s.gdef.board.rows },
		modes: s.gdef.modes.map((m: any) => ({ name: m.name, kind: m.kind, cost: m.cost })),
		testOnly: Boolean(s.gdef.identity.testOnly),
		mode: releaseMode(s.gdef),
		frozenModes: FROZEN_GAMES.has(s.id),
		hasMath: fs.existsSync(path.join(libraryDir(s.id), 'publish_files')),
		requiredSlots: { filled: req.filter((id) => id in lock).length, total: req.length },
	};
};

export const summaries = (): GameSummary[] => listSkins().map(summary);

// ---- validation -----------------------------------------------------------------------------------
export const validate = async (s: SkinRef): Promise<ValidateResult> => {
	const args = [path.join(ROOT, 'tools', 'gamedef', 'validate.py'), path.join(s.dir, 'game.json'), '--json'];
	let stdout = '';
	let stderr = '';
	try {
		({ stdout, stderr } = await run(PY, args, { cwd: ROOT, windowsHide: true, timeout: 120_000, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }));
	} catch (e: any) {
		stdout = e.stdout ?? '';
		stderr = e.stderr ?? e.message;
	}
	try {
		const r = JSON.parse(stdout);
		return { ok: Boolean(r.ok), errors: r.errors ?? [], warnings: r.warnings ?? [] };
	} catch {
		return { ok: false, errors: [{ path: '', message: `validate.py did not answer: ${(stderr || stdout).trim().slice(0, 500)}` }], warnings: [] };
	}
};

// ---- definition -----------------------------------------------------------------------------------
const textPath = (s: SkinRef) => path.join(s.dir, 'text', 'en.json');

export const readDefinition = (s: SkinRef): Definition => {
	const g = readJson(path.join(s.dir, 'game.json'));
	const texts = fs.existsSync(textPath(s)) ? readJson<Record<string, string>>(textPath(s)) : {};
	const frozen = FROZEN_GAMES.has(s.id);
	return {
		identity: { displayName: g.identity.displayName, version: g.identity.version },
		theme: g.theme ?? {},
		texts,
		release: { mode: releaseMode(g) },
		readOnly: { modes: frozen, math: frozen },
	};
};

const isPlainObject = isObj;
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

/** Check an incoming Definition; returns a plain error message or null. Only displayName, version, theme,
 *  release.mode and the values of existing text keys may change; readOnly is server-owned and must not change.
 *  release may be left out (keeps the current mode). */
export const checkDefinition = (s: SkinRef, d: any): string | null => {
	if (!isPlainObject(d)) return 'body must be a Definition object';
	const extra = Object.keys(d).filter((k) => !['identity', 'theme', 'texts', 'release', 'readOnly'].includes(k));
	if (extra.length) return `only identity, theme, texts and release can be edited (got: ${extra.join(', ')})`;
	if (d.release !== undefined) {
		if (!isPlainObject(d.release) || Object.keys(d.release).some((k) => k !== 'mode')) return 'release must be {mode}';
		if (d.release.mode !== 'test' && d.release.mode !== 'release') return "release.mode: 'test' or 'release'";
	}
	if (!isPlainObject(d.identity)) return 'identity must be an object';
	const idExtra = Object.keys(d.identity).filter((k) => !['displayName', 'version'].includes(k));
	if (idExtra.length) return `only identity.displayName and identity.version can be edited (got: ${idExtra.join(', ')})`;
	if (typeof d.identity.displayName !== 'string' || d.identity.displayName.trim().length < 2 || d.identity.displayName.trim().length > 40)
		return 'display name: 2-40 characters';
	if (typeof d.identity.version !== 'string' || !/^\d+\.\d+\.\d+$/.test(d.identity.version)) return 'version: three numbers like 1.2.3';
	if (!isPlainObject(d.theme)) return 'theme must be an object';
	if (!isPlainObject(d.texts)) return 'texts must be an object of strings';
	const cur = readDefinition(s);
	const keysNow = Object.keys(cur.texts).sort();
	const keysIn = Object.keys(d.texts).sort();
	if (!same(keysNow, keysIn)) return 'text keys cannot be added or removed here; only their wording can change';
	for (const [k, v] of Object.entries(d.texts)) if (typeof v !== 'string') return `text '${k}' must be a string`;
	if (d.readOnly !== undefined && !same(d.readOnly, cur.readOnly)) return 'readOnly is set by the editor and cannot be changed';
	return null;
};

/** Snapshot, write the editable fields, then validate. Throws Error with a plain message on refusal. */
export const writeDefinition = async (s: SkinRef, d: Definition): Promise<{ validation: ValidateResult; snapshot: string | null }> => {
	const refusal = checkDefinition(s, d);
	if (refusal) throw new Error(refusal);
	const gPath = path.join(s.dir, 'game.json');
	const gText = fs.readFileSync(gPath, 'utf-8');
	const g = JSON.parse(gText);
	g.identity.displayName = d.identity.displayName.trim();
	g.identity.version = d.identity.version;
	g.theme = d.theme;
	// release.mode: targeted write. Nothing is written when the mode is unchanged (a game without the block stays
	// without it, e.g. Oracle = release); a missing block is appended at the end of game.json.
	const wantMode = d.release?.mode ?? releaseMode(g);
	const addRelease = wantMode !== releaseMode(g) && !isPlainObject(g.release);
	if (wantMode !== releaseMode(g) && !addRelease) g.release = { ...g.release, mode: wantMode };
	let newG = rewrite(gText, g);
	if (addRelease) newG = appendKey(newG, 'release', { mode: wantMode });
	const tText = fs.existsSync(textPath(s)) ? fs.readFileSync(textPath(s), 'utf-8') : null;
	const newT = tText === null ? null : rewrite(tText, { ...JSON.parse(tText), ...d.texts });
	const changed = newG !== gText || (newT !== null && newT !== tText);
	let ts: string | null = null;
	if (changed) {
		ts = snapshot(s.dir);
		if (newG !== gText) fs.writeFileSync(gPath, newG, 'utf-8');
		if (newT !== null && newT !== tText) fs.writeFileSync(textPath(s), newT, 'utf-8');
	}
	return { validation: await validate(s), snapshot: ts };
};
