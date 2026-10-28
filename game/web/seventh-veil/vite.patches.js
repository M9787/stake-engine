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
