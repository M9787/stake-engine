// Replaces the webfontloader package (aliased in vite.config.js). The original loads
// fonts from Typekit, an external request that Stake Engine forbids. Fonts are bundled
// (src/assets/fonts/fonts.css); this waits for them, then calls the same callbacks.
const load = (config) => {
	const fonts = typeof document !== 'undefined' ? document.fonts : undefined;
	if (!fonts) return config.active?.();
	Promise.all([fonts.load('400 16px proxima-nova'), fonts.load('700 16px proxima-nova')])
		.then(() => config.active?.())
		.catch(() => config.inactive?.());
};

export default { load };
export { load };
