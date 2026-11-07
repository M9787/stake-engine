// Asset desk data (docs/10 plan v3.3 sections 3, 12 [P2 P5 P6 P8], 13, 14). Thin layer over the CLI:
// prompts.py renders build/<id>/prompts.json, check_art_in.py --json says what is complete. This file only
// merges their output with assets.lock.json, art_in/provenance.json and art_signoff.json, and writes the
// owner's uploads and provenance lines into skins/<skin>/art_in/ (nothing else).
import { execFile } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { promisify } from 'node:util';

import type { SlotCard, Sitting } from '$lib/types';
import type { Desk, DeskCard } from '$lib/components/assets/desk';

export type { Desk, DeskCard };
import { PY, PY_ASSETS, ROOT, buildDir, inside, readJson, skinOf, type SkinRef } from './repo';

const run = promisify(execFile);

export const LANES = ['raw', 'edited'] as const;
export type Lane = (typeof LANES)[number];

// Accepted upload extensions per slot kind (task spec); the catalogue's full list is used when clearing.
export const UPLOAD_EXT: Record<SlotCard['kind'], string[]> = {
	image: ['.png', '.jpg', '.jpeg', '.webp'],
	music: ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
	sfx: ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
	font: ['.ttf', '.otf'],
};
// tools/assets/catalog.py EXT (catalog.find order): every extension the tools would pick up.
const CATALOG_EXT: Record<SlotCard['kind'], string[]> = {
	image: ['.png', '.jpg', '.jpeg', '.webp'],
	music: ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aiff'],
	sfx: ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aiff'],
	font: ['.ttf', '.otf'],
};
export const MAX_UPLOAD = 60 * 1024 * 1024;

export const CONTENT_TYPE: Record<string, string> = {
	'.png': 'image/png',
	'.jpg': 'image/jpeg',
	'.jpeg': 'image/jpeg',
	'.webp': 'image/webp',
	'.wav': 'audio/wav',
	'.mp3': 'audio/mpeg',
	'.ogg': 'audio/ogg',
	'.flac': 'audio/flac',
	'.m4a': 'audio/mp4',
	'.aiff': 'audio/aiff',
	'.ttf': 'font/ttf',
	'.otf': 'font/otf',
};

const artIn = (s: SkinRef) => path.join(s.dir, 'art_in');
const provPath = (s: SkinRef) => path.join(artIn(s), 'provenance.json');
const mtime = (p: string) => (fs.existsSync(p) ? fs.statSync(p).mtimeMs : 0);

type PromptSlot = {
	id: string;
	kind: SlotCard['kind'];
	sitting: number;
	required: SlotCard['required'];
	px: [number, number] | null;
	aspect: string | null;
	variants: number | null;
	tool: string | null;
	toolLabel: string;
	toolUrl: string;
	steps: string[];
	licenceDefault: string;
	humanEdit: SlotCard['humanEdit'];
	editRecipe: string[];
	source: string;
	prompt: string;
	promptSha: string;
	feeds: string[];
};
type Prompts = { game: string; licences: string[]; slots: PromptSlot[] };
type Provenance = {
	game?: string;
	savedAt?: string;
	minutes?: Record<string, number | string>;
	slots?: Record<string, { licence?: string; sourceUrl?: string; editNote?: string; redo?: string; promptSha?: string }>;
};

/** build/<id>/prompts.json, re-rendered by prompts.py when missing or older than its inputs. */
export async function prompts(s: SkinRef): Promise<Prompts> {
	const out = path.join(buildDir(s.id), 'prompts.json');
	const inputs = [
		path.join(s.dir, 'assets.json'),
		path.join(s.dir, 'game.json'),
		path.join(s.dir, 'text', 'en.json'),
		path.join(ROOT, 'core', 'assets', 'slots.v1.json'),
		path.join(ROOT, 'core', 'assets', 'tools.v1.json'),
	];
	const have = mtime(out);
	if (!have || inputs.some((p) => mtime(p) > have)) {
		try {
			await run(PY, [path.join(ROOT, 'tools', 'assets', 'prompts.py'), '--game', s.id], {
				cwd: ROOT,
				windowsHide: true,
				env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
			});
		} catch (e) {
			// prompts.py exits 1 on lint problems but still writes prompts.json; only a missing/stale file is fatal.
			if (mtime(out) <= have) throw new Error(`Could not render the prompts: ${String((e as { stdout?: string }).stdout || (e as Error).message).trim().slice(0, 400)}`);
		}
	}
	return readJson<Prompts>(out);
}

type Check = { required: { filled: number; total: number }; unknownFiles: string[]; slots: Record<string, { complete: boolean; issues: string[] }> };

async function checkArtIn(s: SkinRef): Promise<Check> {
	try {
		const { stdout } = await run(PY_ASSETS, [path.join(ROOT, 'tools', 'assets', 'check_art_in.py'), '--game', s.id, '--json'], {
			cwd: ROOT,
			windowsHide: true,
			maxBuffer: 16 * 1024 * 1024,
			env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
		});
		return JSON.parse(stdout.trim().split(/\r?\n/).pop() ?? '{}') as Check;
	} catch (e) {
		const err = e as { stderr?: string; message: string };
		throw new Error(`The art check did not run: ${String(err.stderr || err.message).trim().slice(-400)}`);
	}
}

export const readProvenance = (s: SkinRef): Provenance => (fs.existsSync(provPath(s)) ? readJson<Provenance>(provPath(s)) : {});

const readLock = (s: SkinRef): { slots: Record<string, { file?: string }> } => {
	const p = path.join(s.dir, 'assets.lock.json');
	return fs.existsSync(p) ? readJson(p) : { slots: {} };
};

/** art_in/<lane>/<slot>.<ext> as catalog.find would pick it (first extension in catalogue order). */
export function findLane(s: SkinRef, slot: { id: string; kind: SlotCard['kind'] }, lane: Lane): string | null {
	for (const ext of CATALOG_EXT[slot.kind]) {
		const p = path.join(artIn(s), lane, slot.id + ext);
		if (fs.existsSync(p)) return p;
	}
	return null;
}

/** Final file from assets.lock.json (written only by ingest.py), or null. */
export function finalFile(s: SkinRef, slotId: string): string | null {
	const rec = readLock(s).slots?.[slotId];
	if (!rec?.file) return null;
	const p = inside(s.dir, rec.file);
	return fs.existsSync(p) ? p : null;
}

function checklist(): string[] {
	const src = fs.readFileSync(path.join(ROOT, 'tools', 'assets', 'contact_sheet.py'), 'utf-8');
	const block = /CHECKLIST\s*=\s*\[([\s\S]*?)\n\]/.exec(src)?.[1] ?? '';
	return [...block.matchAll(/"((?:[^"\\]|\\.)*)"/g)].map((m) => m[1]);
}

function sittings(): Sitting[] {
	const core = readJson<{ sittings: Sitting[] }>(path.join(ROOT, 'core', 'assets', 'slots.v1.json'));
	return core.sittings.map(({ id, title, minutes, note }) => ({ id, title, minutes, note }));
}

function signoff(s: SkinRef) {
	const p = path.join(s.dir, 'art_signoff.json');
	if (!fs.existsSync(p)) return null;
	const rec = readJson<{ signedBy: string; date: string }>(p);
	// The signed hash covers the best art_in file per slot; any newer file there makes it stale.
	const signed = mtime(p);
	let current = true;
	for (const lane of LANES) {
		const dir = path.join(artIn(s), lane);
		if (!fs.existsSync(dir)) continue;
		for (const f of fs.readdirSync(dir)) if (mtime(path.join(dir, f)) > signed) current = false;
	}
	return { signedBy: rec.signedBy, date: rec.date, current };
}

/** Assemble the whole desk for one game. Throws Error for an unknown game. */
export async function buildDesk(game: string): Promise<Desk> {
	const s = skinOf(game);
	const [p, check] = await Promise.all([prompts(s), checkArtIn(s)]);
	const prov = readProvenance(s);
	const lock = readLock(s);
	const slots: DeskCard[] = p.slots.map((x) => {
		const pv = prov.slots?.[x.id] ?? {};
		const raw = findLane(s, x, 'raw');
		const edited = findLane(s, x, 'edited');
		const c = check.slots?.[x.id] ?? { complete: false, issues: ['not checked'] };
		return {
			id: x.id,
			kind: x.kind,
			sitting: x.sitting,
			required: x.required,
			px: x.px ?? null,
			aspect: x.aspect ?? null,
			variants: x.variants ?? null,
			toolLabel: x.toolLabel,
			toolUrl: x.toolUrl,
			steps: x.steps.map((t) => t.replaceAll('<slot>', x.id)),
			humanEdit: x.humanEdit,
			editRecipe: x.editRecipe ?? [],
			source: x.source ?? '',
			prompt: x.prompt,
			promptSha: x.promptSha,
			feeds: x.feeds ?? [],
			have: { raw: raw ? path.basename(raw) : null, edited: edited ? path.basename(edited) : null },
			ingested: !!lock.slots?.[x.id],
			complete: c.complete,
			issues: c.issues,
			provenance: { licence: pv.licence, sourceUrl: pv.sourceUrl, editNote: pv.editNote, redo: pv.redo },
			tool: x.tool ?? '',
			licenceDefault: x.licenceDefault ?? '',
			drift: !!pv.promptSha && pv.promptSha !== x.promptSha,
		};
	});
	const minutesLogged: Record<string, number> = {};
	for (const [k, v] of Object.entries(prov.minutes ?? {})) {
		const n = Number(v);
		if (Number.isFinite(n) && n > 0) minutesLogged[k] = n;
	}
	const assets = fs.existsSync(path.join(s.dir, 'assets.json')) ? readJson<any>(path.join(s.dir, 'assets.json')) : {};
	const tools = readJson<any>(path.join(ROOT, 'core', 'assets', 'tools.v1.json')).tools ?? {};
	const sunoSlots = slots.filter((x) => x.tool === 'suno');
	return {
		game,
		sittings: sittings(),
		slots,
		licences: p.licences,
		required: check.required,
		signoff: signoff(s),
		sref: typeof assets?.style?.sref === 'string' && assets.style.sref.trim() ? assets.style.sref : null,
		minutesLogged,
		suno: { needed: sunoSlots.length, have: sunoSlots.filter((x) => x.have.raw).length, limit: tools.suno?.monthlyDownloads ?? null },
		unknownFiles: check.unknownFiles ?? [],
		checklist: checklist(),
		contact: ['land', 'port', 'all'].filter((n) => fs.existsSync(path.join(buildDir(game), `contact_${n}.png`))),
	};
}

export async function cardOf(game: string, slot: string): Promise<DeskCard> {
	const card = (await buildDesk(game)).slots.find((c) => c.id === slot);
	if (!card) throw new Error(`unknown slot '${slot}'`);
	return card;
}

/** The prompts.json slot, or throws (validates slot ids against the rendered catalogue). */
export async function slotOf(s: SkinRef, slot: string): Promise<PromptSlot> {
	const x = (await prompts(s)).slots.find((v) => v.id === slot);
	if (!x) throw new Error(`unknown slot '${slot}'`);
	return x;
}

/** Write an upload to art_in/<lane>/<slot>.<ext>, removing the same slot/lane under other extensions. */
export async function saveUpload(game: string, slot: string, lane: Lane, fileName: string, bytes: Uint8Array): Promise<void> {
	const s = skinOf(game);
	const x = await slotOf(s, slot);
	const ext = path.extname(fileName).toLowerCase();
	const ok = UPLOAD_EXT[x.kind];
	if (!ok.includes(ext)) throw new Error(`This ${x.kind} slot takes ${ok.join(', ')} files, not '${ext || 'no extension'}'.`);
	if (bytes.byteLength === 0) throw new Error('The file is empty.');
	if (bytes.byteLength > MAX_UPLOAD) throw new Error('The file is larger than 60 MB.');
	const dir = inside(artIn(s), lane);
	fs.mkdirSync(dir, { recursive: true });
	const dst = inside(dir, slot + ext);
	const tmp = dst + '.part';
	fs.writeFileSync(tmp, bytes);
	for (const e of CATALOG_EXT[x.kind]) {
		const other = inside(dir, slot + e);
		if (e !== ext && fs.existsSync(other)) fs.rmSync(other);
	}
	fs.renameSync(tmp, dst);
}

export type ProvenanceInput = { slot?: string; licence?: string; sourceUrl?: string; editNote?: string; redo?: string; sitting?: number; minutes?: number };

/** Update art_in/provenance.json in the prompts.html export format. A slot line always carries the slot's
 *  current promptSha; {sitting, minutes} logs owner minutes for a sitting. */
export async function saveProvenance(game: string, body: ProvenanceInput): Promise<void> {
	const s = skinOf(game);
	const prov = readProvenance(s);
	const doc: Required<Provenance> = {
		game,
		savedAt: new Date().toISOString(),
		minutes: prov.minutes ?? {},
		slots: prov.slots ?? {},
	};
	if (body.sitting !== undefined) {
		const sid = Number(body.sitting);
		const m = Number(body.minutes);
		if (!Number.isInteger(sid) || !sittings().some((x) => x.id === sid)) throw new Error('unknown sitting');
		if (!Number.isFinite(m) || m < 0 || m > 10000) throw new Error('minutes must be a number from 0 to 10000');
		doc.minutes[String(sid)] = m;
	}
	if (body.slot !== undefined) {
		const p = await prompts(s);
		const x = p.slots.find((v) => v.id === body.slot);
		if (!x) throw new Error(`unknown slot '${body.slot}'`);
		const cur = { ...(doc.slots[x.id] ?? {}) };
		const text = (k: 'licence' | 'sourceUrl' | 'editNote' | 'redo', max: number) => {
			const v = body[k];
			if (v === undefined) return;
			if (typeof v !== 'string') throw new Error(`${k} must be text`);
			const t = v.trim();
			if (t.length > max) throw new Error(`${k} is too long (max ${max} characters)`);
			if (t) cur[k] = t;
			else delete cur[k];
		};
		if (body.licence && !p.licences.includes(body.licence)) throw new Error(`licence '${body.licence}' is not on the allowed list`);
		text('licence', 40);
		text('sourceUrl', 600);
		text('editNote', 600);
		text('redo', 400);
		cur.promptSha = x.promptSha;
		doc.slots[x.id] = cur;
		doc.slots = Object.fromEntries(Object.entries(doc.slots).sort(([a], [b]) => a.localeCompare(b)));
	}
	if (body.slot === undefined && body.sitting === undefined) throw new Error('nothing to save: give a slot or a sitting');
	const dst = provPath(s);
	fs.mkdirSync(path.dirname(dst), { recursive: true });
	fs.writeFileSync(dst + '.part', JSON.stringify(doc, null, 2) + '\n', 'utf-8');
	fs.renameSync(dst + '.part', dst);
}

/** Path of a slot's file for a lane (raw|edited from art_in, final from the lock). */
export async function laneFile(game: string, slot: string, lane: Lane | 'final'): Promise<string | null> {
	const s = skinOf(game);
	const x = await slotOf(s, slot);
	return lane === 'final' ? finalFile(s, x.id) : findLane(s, x, lane);
}

/** Map a thrown Error to an HTTP status for the asset routes (404 unknown game/slot, else 400). */
export const statusOf = (e: unknown) => (/^unknown (game|slot)/.test((e as Error)?.message ?? '') ? 404 : 400);
