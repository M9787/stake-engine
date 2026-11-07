import path from 'node:path';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const repoRoot = path.resolve(import.meta.dirname, '..');

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: '127.0.0.1', // local only: the editor runs tools on this machine
		port: 5174,
		strictPort: true,
		fs: { allow: [repoRoot] },
	},
});
