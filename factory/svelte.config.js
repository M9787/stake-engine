// Factory editor (docs/10 plan v3.3, M12). Runs only as the local Vite dev server on 127.0.0.1:5174;
// it is never built or deployed, so there is no adapter.
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
	preprocess: vitePreprocess(),
	kit: {
		// Same-origin check on POST requests stays on (SvelteKit default csrf.checkOrigin).
	},
};
