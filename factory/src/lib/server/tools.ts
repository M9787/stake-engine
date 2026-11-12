// Whitelist of the CLI tools the editor may run (plan v3.3: the editor is a thin UI over the CLI;
// one code path). Nothing outside this table can be started from the UI.
import fs from 'node:fs';
import path from 'node:path';

import type { JobOpts, ToolId } from '$lib/types';
import { PY, PY_ASSETS, ROOT, FROZEN_GAMES, skinOf } from './repo';

export type ToolSpec = {
	label: string; // shown on buttons
	exe: string;
	args: (game: string, opts: JobOpts) => string[];
	cwd?: string;
	env?: Record<string, string> | ((game: string) => Record<string, string>); // a function gets the game id
	minutes: number; // rough duration for the UI
	service?: boolean; // long-running server (preview): stays up until cancelled
	refuseFrozen?: boolean; // not allowed for frozen games (Oracle math)
};

const ps = (file: string, ...extra: string[]) => ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(ROOT, file), ...extra];
const POWERSHELL = 'powershell.exe';

/** skins/<skin>/math/lookups when the game's weights are frozen (tools/math/freeze.py), else null. */
export const frozenLookups = (game: string): string | null => {
	try {
		const dir = path.join(skinOf(game).dir, 'math', 'lookups');
		return fs.existsSync(dir) ? dir : null;
	} catch {
		return null;
	}
};
/** Math run env: frozen weights are reused automatically (only the books are re-simulated). Frozen tables
 *  have one row per full-run book, so a frozen game's estimate also runs the full sim count (no CT_TIER). */
const mathEnv = (tier: 'preview' | 'candidate') => (game: string): Record<string, string> => {
	const lookups = frozenLookups(game);
	if (lookups) return { PYTHONHASHSEED: '0', CT_REUSE_WEIGHTS: lookups };
	return tier === 'preview' ? { PYTHONHASHSEED: '0', CT_TIER: 'preview' } : { PYTHONHASHSEED: '0' };
};

export const TOOLS: Record<ToolId, ToolSpec> = {
	sync: { label: 'Sync core + skin', exe: POWERSHELL, args: (g) => ps('scripts\\sync.ps1', '-Game', g), minutes: 1 },
	prompts: { label: 'Render prompts', exe: PY, args: (g) => [path.join(ROOT, 'tools\\assets\\prompts.py'), '--game', g], minutes: 0.2 },
	check_art_in: { label: 'Check art files', exe: PY_ASSETS, args: (g) => [path.join(ROOT, 'tools\\assets\\check_art_in.py'), '--game', g], minutes: 0.2 },
	ingest_all: { label: 'Ingest all files', exe: PY_ASSETS, args: (g) => [path.join(ROOT, 'tools\\assets\\ingest.py'), '--game', g, '--all'], minutes: 3 },
	ingest_slot: {
		label: 'Ingest slot',
		exe: PY_ASSETS,
		args: (g, o) => [path.join(ROOT, 'tools\\assets\\ingest.py'), '--game', g, '--slot', String(o.slot)],
		minutes: 0.5,
	},
	contact_sheet: { label: 'Contact sheet', exe: PY_ASSETS, args: (g) => [path.join(ROOT, 'tools\\assets\\contact_sheet.py'), '--game', g], minutes: 0.5 },
	sign_off: {
		label: 'Sign off art',
		exe: PY_ASSETS,
		args: (g, o) => [path.join(ROOT, 'tools\\assets\\contact_sheet.py'), '--game', g, '--sign', String(o.signer)],
		minutes: 0.5,
	},
	audio: { label: 'Build audio sprite', exe: PY_ASSETS, args: (g) => [path.join(ROOT, 'tools\\assets\\audio.py'), '--game', g], minutes: 1 },
	math_preview: {
		label: 'Math preview (10k sims, estimate)',
		exe: PY,
		args: (g) => [`games\\${g}\\run.py`],
		cwd: path.join(ROOT, 'math-sdk'),
		env: mathEnv('preview'),
		minutes: 3,
		refuseFrozen: true,
	},
	math_candidate: {
		label: 'Math candidate (100k sims, full optimizer)',
		exe: PY,
		args: (g) => [`games\\${g}\\run.py`],
		cwd: path.join(ROOT, 'math-sdk'),
		env: mathEnv('candidate'),
		minutes: 40,
		refuseFrozen: true,
	},
	fe_config: { label: 'Math -> web config', exe: PY, args: (g) => [path.join(ROOT, 'scripts\\gen_fe_config.py'), '--game', g], minutes: 0.2 },
	mock: { label: 'Preview data (mock books)', exe: PY, args: (g) => [path.join(ROOT, 'scripts\\books_to_mock.py'), '--game', g], minutes: 1 },
	web_build: { label: 'Build web', exe: POWERSHELL, args: (g) => ps('tools\\web_build.ps1', '-Game', g), minutes: 1 },
	gate_fast: { label: 'Check (fast gate)', exe: POWERSHELL, args: (g) => ps('tools\\gates\\gate.ps1', '-Game', g, '-Fast', '-PreArt'), minutes: 8 },
	gate_full: { label: 'Check (full gate)', exe: POWERSHELL, args: (g) => ps('tools\\gates\\gate.ps1', '-Game', g), minutes: 45 },
	package: { label: 'Package for Stake', exe: POWERSHELL, args: (g) => ps('tools\\package.ps1', '-Game', g), minutes: 3 },
	preview_server: {
		label: 'Start game preview',
		exe: 'cmd.exe',
		args: () => ['/c', 'pnpm', 'exec', 'vite', 'dev', '--port', '3007', '--strictPort'],
		cwd: path.join(ROOT, 'web-sdk', 'apps', 'cluster-tumble'),
		minutes: 0.5,
		service: true,
	},
};

// Added for factory v2 (plan 2026-11-07); scripts are written by the parallel agents A1-A4.
const presetArgs = (o: JobOpts) => {
	const p = o.preset;
	if (!p) return [];
	return ['--board', p.board, '--volatility', p.volatility, '--wincap', String(p.wincap), '--bonus-one-in', String(p.bonusOneIn), '--modes', p.modes.join(',')];
};
Object.assign(TOOLS, {
	test_assets: { label: 'Fill empty slots with test assets', exe: PY_ASSETS, args: (g: string) => [path.join(ROOT, 'tools\\assets\\test_assets.py'), '--game', g], minutes: 2 },
	clear_test_assets: { label: 'Remove test assets', exe: PY_ASSETS, args: (g: string) => [path.join(ROOT, 'tools\\assets\\test_assets.py'), '--game', g, '--clear'], minutes: 0.5 },
	apply_preset: { label: 'Apply preset', exe: PY, args: (g: string, o: JobOpts) => [path.join(ROOT, 'tools\\gamedef\\apply_preset.py'), '--game', g, ...presetArgs(o)], minutes: 0.2, refuseFrozen: true },
	math_freeze: { label: 'Freeze math (keep these weights)', exe: PY, args: (g: string) => [path.join(ROOT, 'tools\\math\\freeze.py'), '--game', g], minutes: 0.2, refuseFrozen: true },
	event_ids: { label: 'Pick reviewer event IDs', exe: PY, args: (g: string, o: JobOpts) => [path.join(ROOT, 'tools\\release\\pick_event_ids.py'), '--game', g, ...(o.version ? ['--version', o.version] : [])], minutes: 1 },
	shots: { label: 'Screenshots at reviewer sizes', exe: 'cmd.exe', args: (g: string) => ['/c', 'pnpm', 'exec', 'playwright', 'test', 'shots'], cwd: path.join(ROOT, 'tools', 'e2e'), minutes: 2 },
	checklist: { label: 'Stake approval checklist', exe: PY, args: (g: string) => [path.join(ROOT, 'tools\\release\\checklist.py'), '--game', g], minutes: 0.5 },
	pack: { label: 'Build submission pack (documents)', exe: PY, args: (g: string) => [path.join(ROOT, 'tools\\release\\pack.py'), '--game', g, '--dry-run'], minutes: 1 },
} satisfies Partial<Record<ToolId, ToolSpec>>);

export const toolAllowed = (tool: string, game: string): string | null => {
	const spec = Object.hasOwn(TOOLS, tool) ? TOOLS[tool as ToolId] : undefined; // not 'toString' etc. from the prototype
	if (!spec) return `unknown tool '${tool}'`;
	if (spec.refuseFrozen && FROZEN_GAMES.has(game)) return 'This game\'s math is frozen (approved weights); it cannot be re-run from the editor.';
	return null;
};
