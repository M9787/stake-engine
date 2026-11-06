// https://github.com/storybookjs/storybook/issues/29567
// Shared config plus the skin's static folder (plan v3.3 slice 10.3): files are served from
// build\<GAME>\web\static, the same folder the app build uses (svelte.config.js kit.files.assets).
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { main } from 'config-storybook';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
const skinStatic = path.join(repoRoot, 'build', process.env.GAME || 'seventh_veil', 'web', 'static'); // lint-core: allow (default game for local dev)

export default { ...main, staticDirs: [skinStatic] };
