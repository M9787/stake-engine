import fs from 'node:fs';
import path from 'node:path';
import { mergeConfig } from 'vite';
// @ts-ignore
import config from 'config-vite';
import mockRgs from './dev/mockRgs.js';
import { sharedPackagePatches } from './vite.patches.js';

const { version } = JSON.parse(fs.readFileSync(path.resolve('package.json'), 'utf-8'));

// Stake Engine forbids external requests. Sample bet-mode images (S3) and paytable images
// (twist-game.app) in state-shared defaults are never used by this game; blank them so the
// URLs do not reach the bundle.
const stripSampleUrls = () => ({
	name: 'seventh-veil-strip-sample-urls',
	enforce: 'pre',
	transform(code, id) {
		if (!id.replace(/\\/g, '/').includes('state-shared/src/constants')) return null;
		return code.replace(/https:\/\/[^'"`\s]+/g, '');
	},
});

// Dev HTTPS: the SDK always calls https://{rgs_url}. Certificate from scripts/dev_cert.ps1.
const certDir = path.resolve('.mock-rgs');
const https = fs.existsSync(path.join(certDir, 'cert.pem'))
	? { cert: fs.readFileSync(path.join(certDir, 'cert.pem')), key: fs.readFileSync(path.join(certDir, 'key.pem')) }
	: undefined;

export default mergeConfig(config(), {
	plugins: [stripSampleUrls(), sharedPackagePatches(), mockRgs()],
	resolve: {
		alias: [
			{ find: 'webfontloader', replacement: path.resolve('src/stubs/webfontloader.js') },
			// Money formatting for all currencies and sub-cent wins (Engine [219], [273], [78]).
			{ find: /^utils-shared\/amount$/, replacement: path.resolve('src/overrides/amount.ts') },
			// Our social wording, imported by patched shared i18n files (vite.patches.js).
			{ find: /^seventh-veil\/wording$/, replacement: path.resolve('src/game/wording.ts') },
		],
	},
	server: https ? { https } : {},
	// Shown by GameVersion in the menu (package.json version).
	define: { __GAME_VERSION__: JSON.stringify(version) },
});
