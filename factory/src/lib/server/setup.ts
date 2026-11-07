// Game setup (factory v2, plan 2026-11-07): presets (tools/gamedef/apply_preset.py as a job) and the Advanced
// forms (symbols, paytable, modes, features, reel strips, math, review + listing). Every write: history snapshot
// first, targeted JSON write that keeps key order and formatting (games.ts editJson), then validate.py --json.
// Checks here are only shape/type guards; game rules live in validate.py (one code path).
// Math state: tier from math-sdk/games/<id>/library/run_meta.json, stale = hash of the math sections + reel CSVs
// differs from build/<id>/math_stamp.json (written by POST math-state {stamp:true} after a math job).
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

import type { Job, MathState, PresetRequest, ValidateResult } from '$lib/types';
import { editJson, validate } from './games';
import { snapshot } from './history';
import { FROZEN_GAMES, ROOT, buildDir, inside, libraryDir, readJson, type SkinRef } from './repo';
import { startJob } from './jobs';

export const MATH_SECTIONS = ['board', 'symbols', 'paytable', 'reels', 'freespinTriggers', 'features', 'reelWeights', 'modes', 'math'] as const;
const PRESETS = path.join(ROOT, 'core', 'presets');

const isObj = (v: unknown): v is Record<string, any> => !!v && typeof v === 'object' && !Array.isArray(v);
const isNum = (v: unknown, lo = -Infinity, hi = Infinity): v is number => typeof v === 'number' && Number.isFinite(v) && v >= lo && v <= hi;
const isInt = (v: unknown, lo = -Infinity, hi = Infinity): v is number => isNum(v, lo, hi) && Number.isInteger(v);
const isStr = (v: unknown, max = 2000): v is string => typeof v === 'string' && v.length <= max;

class Refusal extends Error {}
const refuse = (msg: string): never => {
	throw new Refusal(msg);
};

// ---- format-preserving rewrite -----------------------------------------------------------------------
type P = (string | number)[];
const sameKeys = (a: object, b: object) => JSON.stringify(Object.keys(a)) === JSON.stringify(Object.keys(b));
const diff = (a: unknown, b: unknown, p: P, out: { p: P; v: unknown }[]) => {
	if (isObj(a) && isObj(b) && sameKeys(a, b)) for (const k of Object.keys(b)) diff(a[k], b[k], [...p, k], out);
	else if (Array.isArray(a) && Array.isArray(b) && a.length === b.length) b.forEach((x, n) => diff(a[n], x, [...p, n], out));
	else if (!(a === b || (typeof a === 'object' && JSON.stringify(a) === JSON.stringify(b)))) out.push({ p, v: b });
};
/** Text of `text` changed to parse as `next`: changed values are spliced in place; new top-level keys are
 *  appended at the end of the root object (key order of `next` otherwise follows the file). */
export const rewrite = (text: string, next: Record<string, unknown>): string => {
	const cur = JSON.parse(text);
	const added = Object.keys(next).filter((k) => !(k in cur));
	const removed = Object.keys(cur).filter((k) => !(k in next));
	if (removed.length) refuse(`cannot remove sections (${removed.join(', ')})`);
	const edits: { p: P; v: unknown }[] = [];
	for (const k of Object.keys(cur)) diff(cur[k], next[k], [k], edits);
	let out = edits.length ? editJson(text, edits) : text;
	if (added.length) {
		const end = out.lastIndexOf('}');
		const body = added.map((k) => `  ${JSON.stringify(k)}: ${JSON.stringify(next[k], null, 2).replace(/\n/g, '\n  ')}`).join(',\n');
		out = out.slice(0, end).replace(/\s*$/, '') + ',\n' + body + '\n' + out.slice(end);
	}
	return out;
};

// ---- reading ------------------------------------------------------------------------------------------
const gamePath = (s: SkinRef) => path.join(s.dir, 'game.json');
const textPath = (s: SkinRef) => path.join(s.dir, 'text', 'en.json');
const reelDir = (s: SkinRef) => path.join(s.dir, 'math', 'reels');
const readTexts = (s: SkinRef): Record<string, string> => (fs.existsSync(textPath(s)) ? readJson(textPath(s)) : {});

export type PresetInfo = { id: string; label: string; explain: string; defaults: { wincap: number; bonusOneIn: number } };
export const presetChoices = () => {
	const vol: PresetInfo[] = ['low', 'medium', 'high'].map((v) => {
		const p = readJson(path.join(PRESETS, 'volatility', `${v}.json`));
		return { id: p.id, label: p.label, explain: p.explain, defaults: p.defaults };
	});
	const boards = Object.keys(readJson(path.join(PRESETS, 'boards.json')).boards);
	return { volatility: vol, boards };
};

export type StripInfo = { id: string; file: string; reels: number; length: number; symbols: string[]; scatters: number; error?: string };
const parseCsv = (text: string): string[][] =>
	text
		.split(/\r?\n/)
		.map((l) => l.trim())
		.filter(Boolean)
		.map((l) => l.split(',').map((c) => c.trim()));
const stripInfo = (s: SkinRef, id: string, file: string): StripInfo => {
	const p = path.join(reelDir(s), file);
	if (!fs.existsSync(p)) return { id, file, reels: 0, length: 0, symbols: [], scatters: 0, error: 'file missing' };
	const rows = parseCsv(fs.readFileSync(p, 'utf-8'));
	const syms = [...new Set(rows.flat())].sort();
	return { id, file, reels: rows[0]?.length ?? 0, length: rows.length, symbols: syms, scatters: rows.flat().filter((c) => c === 'S').length };
};

export const readSetup = (s: SkinRef) => {
	const g = readJson(gamePath(s));
	const texts = readTexts(s);
	const frozen = FROZEN_GAMES.has(s.id);
	return {
		id: s.id,
		skin: s.skin,
		frozen,
		frozenLookups: fs.existsSync(path.join(s.dir, 'math', 'lookups')),
		board: g.board,
		symbols: g.symbols.map((x: any) => ({ ...x, name: texts[x.nameKey] ?? '' })),
		paytable: g.paytable,
		freespinTriggers: g.freespinTriggers,
		features: g.features,
		modes: g.modes.map((m: any) => ({
			...m,
			label: texts[`mode.${m.name}.label`] ?? '',
			title: texts[`mode.${m.name}.title`] ?? '',
		})),
		math: g.math,
		review: g.review,
		listing: g.listing ?? {},
		strips: Object.entries(g.reels.files as Record<string, string>).map(([id, f]) => stripInfo(s, id, f)),
		presets: presetChoices(),
	};
};

// ---- writing ------------------------------------------------------------------------------------------
type WriteResult = { validation: ValidateResult; snapshot: string | null };

/** Snapshot, write game.json (and texts / extra files when given) if anything changed, then validate. */
const commit = async (s: SkinRef, g: Record<string, unknown>, texts?: Record<string, string>, files?: { p: string; data: string }[]): Promise<WriteResult> => {
	const gText = fs.readFileSync(gamePath(s), 'utf-8');
	const newG = rewrite(gText, g);
	const tText = fs.existsSync(textPath(s)) ? fs.readFileSync(textPath(s), 'utf-8') : null;
	let newT = tText;
	if (texts && tText !== null) {
		const cur = JSON.parse(tText);
		const reordered = JSON.stringify(Object.keys(cur)) !== JSON.stringify(Object.keys(texts).filter((k) => k in cur));
		newT = Object.keys(cur).some((k) => !(k in texts)) || reordered ? JSON.stringify(texts, null, 2) + '\n' : rewrite(tText, texts);
	}
	const fileChanges = (files ?? []).filter((f) => !fs.existsSync(f.p) || fs.readFileSync(f.p, 'utf-8') !== f.data);
	const changed = newG !== gText || newT !== tText || fileChanges.length > 0;
	let ts: string | null = null;
	if (changed) {
		ts = snapshot(s.dir);
		if (newG !== gText) fs.writeFileSync(gamePath(s), newG, 'utf-8');
		if (newT !== null && newT !== tText) fs.writeFileSync(textPath(s), newT, 'utf-8');
		for (const f of fileChanges) fs.writeFileSync(f.p, f.data, 'utf-8');
	}
	return { validation: await validate(s), snapshot: ts };
};

export const SECTIONS = ['symbols', 'paytable', 'modes', 'features', 'math', 'review'] as const;
export type Section = (typeof SECTIONS)[number];
const TEXT_ONLY: Section[] = ['review']; // allowed for frozen games (no math change)

const countMap = (v: unknown, what: string, lo = 0) => {
	if (!isObj(v)) refuse(`${what}: expected scatter counts`);
	const out: Record<string, number> = {};
	for (const [k, n] of Object.entries(v as object)) {
		if (!/^\d{1,2}$/.test(k) || !isInt(n, lo, 1000)) refuse(`${what}: '${k}' must be a count with a whole number`);
		out[String(Number(k))] = n as number;
	}
	return out;
};
const pair = (v: unknown, what: string): [number, number] => {
	if (!Array.isArray(v) || v.length !== 2 || !isNum(v[0]) || !isNum(v[1])) refuse(`${what}: two numbers`);
	return [(v as number[])[0], (v as number[])[1]];
};
const scaleRules = (v: unknown, what: string) => {
	if (!Array.isArray(v)) refuse(`${what}: a list of [[from, to], factor]`);
	return (v as unknown[]).map((r, i) => {
		if (!Array.isArray(r) || r.length !== 2 || !isNum(r[1], 0.0001, 1000)) refuse(`${what} #${i + 1}: [[from, to], factor > 0]`);
		return [pair((r as unknown[])[0], `${what} #${i + 1}`), (r as number[])[1]];
	});
};

/** Texts of renamed modes move to the new key in the same position, with their {mode.<old>.x} placeholders
 *  rewritten; a value already given for the new key (form label/title) wins. */
const renameModeTexts = (texts: Record<string, string>, renames: Map<string, string>): Record<string, string> => {
	const out: Record<string, string> = {};
	const fix = (v: string) => {
		if (typeof v !== 'string') return v;
		for (const [a, b] of renames) v = v.replaceAll(`{mode.${a}.`, `{mode.${b}.`);
		return v;
	};
	for (const [k, v] of Object.entries(texts)) {
		const m = /^mode\.([^.]+)\.(.+)$/.exec(k);
		const to = m ? renames.get(m[1]) : undefined;
		if (!to) {
			if (!(k in out)) out[k] = fix(v);
			continue;
		}
		const nk = `mode.${to}.${m![2]}`;
		out[nk] = fix(Object.hasOwn(texts, nk) ? texts[nk] : v);
	}
	return out;
};

/** Apply one Advanced form. Throws Refusal with a plain message. */
export const saveSection = async (s: SkinRef, section: string, body: any): Promise<WriteResult> => {
	if (!(SECTIONS as readonly string[]).includes(section)) refuse(`unknown section '${section}'`);
	const sec = section as Section;
	if (FROZEN_GAMES.has(s.id) && !TEXT_ONLY.includes(sec))
		refuse('This is an approved game: its symbols, paytable, modes, features and math are frozen and cannot be changed.');
	if (!isObj(body)) refuse('body must be a JSON object');
	const g = readJson(gamePath(s));
	const texts = readTexts(s);
	let newTexts: Record<string, string> | undefined;

	if (sec === 'symbols') {
		// Ids and roles stay (they tie into reels and paytable); tier of pay symbols and display names change.
		if (!Array.isArray(body.symbols) || body.symbols.length !== g.symbols.length) refuse('send every symbol once');
		newTexts = { ...texts };
		g.symbols = g.symbols.map((cur: any, i: number) => {
			const x = body.symbols[i];
			if (!isObj(x) || x.id !== cur.id) refuse('symbols must keep their ids and order');
			if (x.role !== undefined && x.role !== cur.role) refuse(`${cur.id}: the role cannot change here (use a preset)`);
			const next = { ...cur };
			if (cur.role === 'pay') {
				if (x.tier !== 'high' && x.tier !== 'low') refuse(`${cur.id}: tier must be high or low`);
				next.tier = x.tier;
			}
			if (x.name !== undefined) {
				if (!isStr(x.name, 40) || x.name.trim().length < 1) refuse(`${cur.id}: name 1-40 characters`);
				newTexts![cur.nameKey] = x.name.trim();
			}
			return next;
		});
	} else if (sec === 'paytable') {
		const pt = body.paytable;
		if (!isObj(pt) || !Array.isArray(pt.bands) || !isObj(pt.pays)) refuse('paytable: {bands, pays}');
		if (pt.bands.length < 1 || pt.bands.length > 8) refuse('1 to 8 cluster-size bands');
		const bands = pt.bands.map((b: unknown, i: number) => {
			const [lo, hi] = pair(b, `band #${i + 1}`);
			if (!isInt(lo, 2, 64) || !isInt(hi, 2, 64)) refuse(`band #${i + 1}: whole numbers 2-64`);
			return [lo, hi];
		});
		const payIds = g.symbols.filter((x: any) => x.role === 'pay').map((x: any) => x.id);
		const pays: Record<string, number[]> = {};
		for (const sid of payIds) {
			const row = pt.pays[sid];
			if (!Array.isArray(row) || row.length !== bands.length || !row.every((v: unknown) => isNum(v, 0.01, 100000)))
				refuse(`${sid}: one win per band, each 0.01-100000`);
			pays[sid] = row;
		}
		if (Object.keys(pt.pays).some((k) => !payIds.includes(k))) refuse('wins given for a symbol that is not a pay symbol');
		g.paytable = { ...g.paytable, bands, pays, minPay: Math.min(...Object.values(pays).flat()) };
	} else if (sec === 'modes') {
		if (!Array.isArray(body.modes) || body.modes.length !== g.modes.length) refuse('send every mode once (add or remove modes with a preset)');
		const newSims: Record<string, number> = {};
		const newTargets: Record<string, unknown> = {};
		newTexts = { ...texts };
		const pres = isObj(g.presentation?.modes) ? { ...g.presentation.modes } : null;
		const renames = new Map<string, string>(); // old mode name -> new
		g.modes = g.modes.map((cur: any, i: number) => {
			const x = body.modes[i];
			if (!isObj(x) || x.from !== cur.name) refuse('modes must keep their order (each card names the mode it came from)');
			if (x.kind !== cur.kind) refuse(`${cur.name}: the kind (spin or bonus) cannot change here; use a preset`);
			if (!isStr(x.name, 32) || !/^[A-Za-z0-9_-]{1,32}$/.test(x.name)) refuse(`${cur.name}: name 1-32 letters, digits, _ or -`);
			if (!isNum(x.cost, 1, 50000)) refuse(`${cur.name}: price 1-50000 x bet`);
			const quotas: Record<string, number> = {};
			if (!isObj(x.quotas)) refuse(`${cur.name}: quotas missing`);
			for (const [k, v] of Object.entries(x.quotas)) {
				if (!['wincap', 'freegame', 'zero', 'basegame'].includes(k) || !isNum(v, 0, 1)) refuse(`${cur.name}: quota ${k} must be 0-1`);
				quotas[k] = v as number;
			}
			const trig: Record<string, unknown> = {};
			if (!isObj(x.scatterTriggers)) refuse(`${cur.name}: scatter triggers missing`);
			for (const [k, v] of Object.entries(x.scatterTriggers)) {
				if (!['wincap', 'freegame', 'all'].includes(k)) refuse(`${cur.name}: unknown trigger table ${k}`);
				trig[k] = countMap(v, `${cur.name} ${k} triggers`);
			}
			const next: any = { ...cur, name: x.name, cost: x.cost, quotas, scatterTriggers: trig };
			if (cur.kind === 'buy') {
				if (!isStr(x.variant, 21)) refuse(`${cur.name}: pick a bonus variant`);
				next.variant = x.variant;
			}
			// target
			const t = x.target;
			if (!isObj(t)) refuse(`${cur.name}: math target missing`);
			const tgt: any = { ...(g.math.targets[cur.name] ?? {}), kind: cur.kind };
			for (const k of ['wincapRtp', 'freegameRtp']) {
				if (!isNum(t[k], 0, 1)) refuse(`${cur.name}: ${k} must be 0-1`);
				tgt[k] = t[k];
			}
			if (cur.kind === 'spin') {
				for (const [k, lo, hi] of [['bonusOneIn', 20, 2000], ['hitOneIn', 1.5, 50], ['basegameRtp', 0, 1]] as const) {
					if (!isNum(t[k], lo, hi)) refuse(`${cur.name}: ${k} must be ${lo}-${hi}`);
					tgt[k] = t[k];
				}
				tgt.midWinLift = pair(t.midWinLift, `${cur.name} mid-win lift`);
				tgt.baseScaling = scaleRules(t.baseScaling, `${cur.name} base scaling`);
			} else {
				if (!isNum(t.minM2m, 0.5, 100) || !isNum(t.maxM2m, 1, 100)) refuse(`${cur.name}: spread limits must be numbers`);
				tgt.minM2m = t.minM2m;
				tgt.maxM2m = t.maxM2m;
				tgt.scaling = scaleRules(t.scaling, `${cur.name} scaling`);
			}
			newTargets[x.name] = tgt;
			newSims[x.name] = g.math.sims[cur.name] ?? 100000;
			if (x.name !== cur.name) {
				renames.set(cur.name, x.name);
				if (pres && cur.name in pres) {
					pres[x.name] = pres[cur.name];
					delete pres[cur.name];
				}
			}
			for (const f of ['title', 'label'] as const) {
				if (x[f] !== undefined) {
					if (!isStr(x[f], 60)) refuse(`${cur.name}: ${f} up to 60 characters`);
					newTexts![`mode.${x.name}.${f}`] = x[f];
				}
			}
			return next;
		});
		const names = g.modes.map((m: any) => m.name.toLowerCase());
		if (new Set(names).size !== names.length) refuse('two modes would share a name');
		g.math = { ...g.math, sims: newSims, targets: newTargets };
		if (pres) g.presentation = { ...g.presentation, modes: pres };
		if (renames.size) newTexts = renameModeTexts(newTexts!, renames);
	} else if (sec === 'features') {
		const f = body.features;
		if (!isObj(f) || !isObj(f.gridMultiplier) || !Array.isArray(f.bonusVariants)) refuse('features: {gridMultiplier, bonusVariants}');
		if (typeof f.gridMultiplier.enabled !== 'boolean' || !isInt(f.gridMultiplier.cap, 2, 4096)) refuse('grid: on/off and a cap 2-4096');
		if (f.bonusVariants.length !== g.features.bonusVariants.length) refuse('bonus variants cannot be added or removed here');
		const variants = g.features.bonusVariants.map((cur: any, i: number) => {
			const v = f.bonusVariants[i];
			if (!isObj(v) || v.id !== cur.id) refuse('bonus variants must keep their ids and order');
			if (!isInt(v.scatterMin, 2, 64) || !isInt(v.scatterMax, 2, 64)) refuse(`${cur.id}: scatter range whole numbers 2-64`);
			if (!isObj(v.precharge) || !isInt(v.precharge.spots, 0, 64) || !isInt(v.precharge.value, 2, 1024)) refuse(`${cur.id}: pre-charge spots 0-64, value 2-1024`);
			const next: any = { ...cur, scatterMin: v.scatterMin, scatterMax: v.scatterMax, precharge: { spots: v.precharge.spots, value: v.precharge.value } };
			if (v.buyFloor !== undefined && v.buyFloor !== null) {
				if (!isNum(v.buyFloor, 0, 100000)) refuse(`${cur.id}: lowest bought win must be a number`);
				next.buyFloor = v.buyFloor;
			}
			return next;
		});
		g.features = { ...g.features, gridMultiplier: { ...g.features.gridMultiplier, enabled: f.gridMultiplier.enabled, cap: f.gridMultiplier.cap }, bonusVariants: variants };
		if (body.freespinTriggers !== undefined) {
			const t = body.freespinTriggers;
			if (!isObj(t)) refuse('free spins: {basegame, freegame}');
			g.freespinTriggers = { basegame: countMap(t.basegame, 'free spins from the base game'), freegame: countMap(t.freegame, 'extra spins in the bonus') };
		}
	} else if (sec === 'math') {
		const m = body.math;
		if (!isObj(m) || !isNum(m.rtp, 0.9, 0.99) || !isNum(m.wincap, 100, 1_000_000) || !isObj(m.sims)) refuse('math: {rtp, wincap, sims}');
		const sims: Record<string, number> = {};
		for (const mode of g.modes) {
			if (!isInt(m.sims[mode.name], 10000, 1_000_000)) refuse(`${mode.name}: simulations 10,000-1,000,000`);
			sims[mode.name] = m.sims[mode.name];
		}
		g.math = { ...g.math, rtp: m.rtp, wincap: m.wincap, sims };
	} else if (sec === 'review') {
		const r = body.review;
		if (!isObj(r) || !isStr(r.signatureMoment, 600) || !Array.isArray(r.originality) || !r.originality.every((x: unknown) => isStr(x, 200)))
			refuse('review: {signatureMoment, originality[]}');
		g.review = { ...g.review, signatureMoment: r.signatureMoment, originality: r.originality };
		if (body.listing !== undefined) {
			const l = body.listing;
			if (!isObj(l)) refuse('listing must be an object');
			const next: any = { ...(g.listing ?? {}) };
			if (l.blurb !== undefined) next.blurb = isStr(l.blurb, 600) ? l.blurb : refuse('listing blurb: up to 600 characters');
			if (l.features !== undefined)
				next.features =
					Array.isArray(l.features) && l.features.length <= 10 && l.features.every((x: unknown) => isStr(x, 120))
						? l.features
						: refuse('listing features: up to 10 lines of 120 characters');
			if (l.reviewerNotes !== undefined) next.reviewerNotes = isStr(l.reviewerNotes, 2000) ? l.reviewerNotes : refuse('reviewer notes: up to 2000 characters');
			if (l.distribution !== undefined && l.distribution !== null && l.distribution !== '') {
				if (!['onlyStake', 'network'].includes(l.distribution)) refuse('distribution: Stake only or network');
				next.distribution = l.distribution;
			}
			for (const k of Object.keys(next)) if (next[k] === '' || (Array.isArray(next[k]) && !next[k].length)) delete next[k];
			if (Object.keys(next).length || g.listing) g.listing = next;
		}
	}
	return commit(s, g, newTexts);
};

// ---- reel strips --------------------------------------------------------------------------------------
const stripFile = (s: SkinRef, strip: string): string => {
	const g = readJson(gamePath(s));
	const file = (g.reels.files as Record<string, string>)[strip];
	if (!Object.hasOwn(g.reels.files, strip) || !file) refuse(`unknown reel strip '${strip}'`);
	return inside(reelDir(s), file);
};

export const readStrip = (s: SkinRef, strip: string): { name: string; text: string } => {
	const p = stripFile(s, strip);
	if (!fs.existsSync(p)) refuse('this strip file is missing');
	return { name: path.basename(p), text: fs.readFileSync(p, 'utf-8') };
};

/** Replace one strip with uploaded CSV text (one row per stop, one column per reel). */
export const writeStrip = async (s: SkinRef, strip: string, csv: string): Promise<WriteResult> => {
	if (FROZEN_GAMES.has(s.id)) refuse('This is an approved game: its reel strips are frozen.');
	if (csv.length > 2_000_000) refuse('file too large (2 MB at most)');
	const rows = parseCsv(csv.replace(/^﻿/, ''));
	const g = readJson(gamePath(s));
	const known = new Set(g.symbols.map((x: any) => x.id));
	if (rows.length < 10) refuse('a strip needs at least 10 rows (stops)');
	if (rows.some((r) => r.length !== g.board.reels)) refuse(`every row needs ${g.board.reels} symbols (one per reel)`);
	const unknown = [...new Set(rows.flat().filter((c) => !known.has(c)))];
	if (unknown.length) refuse(`unknown symbols: ${unknown.slice(0, 8).join(', ')}`);
	const p = stripFile(s, strip);
	return commit(s, g, undefined, [{ p, data: rows.map((r) => r.join(',')).join('\n') + '\n' }]);
};

// ---- presets ------------------------------------------------------------------------------------------
export const checkPreset = (p: any): PresetRequest => {
	const choices = presetChoices();
	if (!isObj(p)) refuse('preset missing');
	if (!choices.boards.includes(p.board)) refuse('board: 5x5 to 8x8');
	if (!['low', 'medium', 'high'].includes(p.volatility)) refuse('volatility: low, medium or high');
	if (!isNum(p.wincap, 100, 1_000_000)) refuse('max win: 100 to 1,000,000 x bet');
	if (!isNum(p.bonusOneIn, 20, 2000)) refuse('bonus frequency: 1 in 20 to 1 in 2000 spins');
	if (!Array.isArray(p.modes) || !p.modes.includes('base') || !p.modes.every((m: unknown) => m === 'base' || m === 'ante' || m === 'buy'))
		refuse('modes: base plus optional ante and buy');
	return { board: p.board, volatility: p.volatility, wincap: p.wincap, bonusOneIn: p.bonusOneIn, modes: [...new Set(p.modes as string[])] };
};

/** Snapshot the skin, then start the apply_preset job (the tool itself never snapshots). */
export const startPreset = (s: SkinRef, p: unknown): { job: Job; snapshot: string } => {
	if (FROZEN_GAMES.has(s.id)) refuse('This is an approved game: its modes and math are frozen.');
	const preset = checkPreset(p);
	const ts = snapshot(s.dir);
	return { job: startJob(s.id, 'apply_preset', { preset }), snapshot: ts };
};

// ---- math state ---------------------------------------------------------------------------------------
const canon = (v: unknown): unknown =>
	Array.isArray(v) ? v.map(canon) : isObj(v) ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, canon(v[k])])) : v;

/** sha256 of the math sections of game.json (key order ignored) plus the bytes of every reel CSV it names. */
export const mathHash = (s: SkinRef): string => {
	const g = readJson(gamePath(s));
	const h = crypto.createHash('sha256');
	h.update(JSON.stringify(canon(Object.fromEntries(MATH_SECTIONS.map((k) => [k, g[k] ?? null])))));
	for (const [id, file] of Object.entries((g.reels?.files ?? {}) as Record<string, string>).sort(([a], [b]) => a.localeCompare(b))) {
		h.update(`\0${id}\0`);
		const p = path.join(reelDir(s), file);
		h.update(fs.existsSync(p) ? fs.readFileSync(p) : Buffer.from('missing'));
	}
	return h.digest('hex');
};

const stampPath = (id: string) => path.join(buildDir(id), 'math_stamp.json');

export const mathState = (s: SkinRef): MathState => {
	const meta = path.join(libraryDir(s.id), 'run_meta.json');
	const frozenLookups = fs.existsSync(path.join(s.dir, 'math', 'lookups'));
	let tier: MathState['tier'] = 'none';
	let lastRun: string | null = null;
	if (fs.existsSync(meta)) {
		try {
			tier = readJson(meta).tier === 'preview' ? 'preview' : 'candidate';
		} catch {
			tier = 'candidate';
		}
		lastRun = fs.statSync(meta).mtime.toISOString();
	}
	if (frozenLookups) tier = 'frozen';
	let stale = false;
	const sp = stampPath(s.id);
	if (fs.existsSync(sp)) {
		try {
			const st = readJson(sp);
			stale = st.hash !== mathHash(s);
			lastRun = st.stamped ?? lastRun;
		} catch {
			stale = true;
		}
	}
	// No stamp (math run before stamping existed): unknown, reported as not stale. File times are no help here:
	// a theme or name edit also touches game.json.
	return { tier, stale, lastRun, frozenLookups };
};

/** Record the current math hash as "the math that was just run" (called after a math job finishes). */
export const stampMath = (s: SkinRef): MathState => {
	fs.mkdirSync(buildDir(s.id), { recursive: true });
	const st = mathState(s);
	fs.writeFileSync(stampPath(s.id), JSON.stringify({ hash: mathHash(s), stamped: new Date().toISOString(), tier: st.tier }, null, 2) + '\n', 'utf-8');
	return mathState(s);
};

export const isRefusal = (e: unknown): e is Refusal => e instanceof Refusal;
