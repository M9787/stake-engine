// Build-time patches for shared web-sdk packages (packages are read-only, CLAUDE.md).
// Each patch names the package file it changes and the exact code it replaces.
// If a search pattern is not found (for example after an SDK update), the build FAILS
// instead of silently shipping the unpatched code.

/** @typedef {{ file: string, why: string, edits: [RegExp, string][] }} Patch */

/** @type {Patch[]} */
export const PATCHES = [
	{
		// Engine [239][240]: unknown lang codes fall back to English. One fix for every reader
		// (LoadI18n, Authenticate, localized sprite keys in FreeSpinIntro/Outro, PressToContinue).
		file: 'state-shared/src/stateUrl.svelte.ts',
		why: 'lang fallback to supported list',
		edits: [
			[
				/const lang = \(\) =>\s*getUrlSearchParam\('lang'\) === 'br' \? 'pt' : \(getUrlSearchParam\('lang'\) as Language\) \|\| 'en';/,
				`const SUPPORTED_LANGS: string[] = ['en'];
const lang = () => {
	const raw = (getUrlSearchParam('lang') || '').toLowerCase();
	return (SUPPORTED_LANGS.includes(raw) ? raw : 'en') as Language;
};`,
			],
		],
	},
	{
		// Engine [222]: the real cost of every mode, buy modes included (shared code counts a
		// 100x buy as 1x), and no crash while no mode is set. Also fixes the replay cost [174].
		// Engine [242]: on low balance the bet snaps to a valid bet level, never to balance/cost.
		file: 'state-shared/src/stateBet.svelte.ts',
		why: 'real mode cost and bet-level snapping',
		edits: [
			[
				/import \{ stateMeta \} from '\.\/stateMeta\.svelte';/,
				`import { stateMeta } from './stateMeta.svelte';
import { stateConfig } from './stateConfig.svelte';`,
			],
			[
				/const max = stateBet\.balanceAmount \/ costMultiplier;\s*if \(value >= max\) return max;\s*return value;/,
				`const max = stateBet.balanceAmount / costMultiplier;
	if (value <= max) return value;
	const levels = [...stateConfig.betAmountOptions].sort((a, b) => a - b);
	const fitting = levels.filter((level) => level <= max);
	return fitting.length ? fitting[fitting.length - 1] : (levels[0] ?? value);`,
			],
			[
				/const betCostMultiplier = \(\) =>\s*stateBetDerived\.activeBetMode\(\)\.type === 'activate'\s*\? stateBetDerived\.activeBetMode\(\)\.costMultiplier\s*: 1;/,
				`const betCostMultiplier = () => stateBetDerived.activeBetMode()?.costMultiplier ?? 1;`,
			],
		],
	},
];

export const sharedPackagePatches = () => {
	const applied = new Set();

	return {
		name: 'seventh-veil-shared-package-patches',
		enforce: 'pre',
		buildStart() {
			applied.clear();
		},
		// A patch that never ran means its file moved or is no longer imported. Log it on
		// every build so `scripts` and reviews can spot it (the SSR pass may skip some files).
		buildEnd(error) {
			if (error || this.meta.watchMode) return;
			const missing = PATCHES.filter((p) => !applied.has(p.file)).map((p) => p.file);
			console.log(`[seventh-veil patches] applied ${applied.size}/${PATCHES.length}${missing.length ? `; not applied: ${missing.join(', ')}` : ''}`);
		},
		transform(code, id) {
			const file = id.replace(/\\/g, '/').split('?')[0];
			const patch = PATCHES.find((p) => file.endsWith(`/packages/${p.file}`));
			if (!patch) return null;
			let out = code;
			for (const [search, replace] of patch.edits) {
				search.lastIndex = 0; // global regexes keep state between test() calls
				if (!search.test(out)) {
					throw new Error(`seventh-veil patch "${patch.why}": pattern not found in ${patch.file}: ${search}`);
				}
				out = out.replace(search, replace);
			}
			applied.add(patch.file);
			return { code: out, map: null };
		},
	};
};
