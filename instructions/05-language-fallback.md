# 05 — Language fallback

**Goal:** `?lang=en` shows only English: no keys, no `undefined`, no `NaN`. Unknown codes such as `?lang=xx` or `?lang=en_US` fall back to English without errors.

**Why:** Guidelines [239] and [240] (https://studio.engine.io/docs-content/prompt.md, 2026-10-28).

**Depends on:** 02.

## Current problems (audit 2026-10-28)
- `stateUrl.svelte.ts:27-28` accepts any value.
- `LoadI18n.svelte:23-33` falls back only when `init` throws, and `xx` does not throw.
- The result is missing textures: `freespins_xx.png`, `winsmall_xx.png` and `pressToContinueText_xx.png` (`FreeSpinIntro.svelte:51`, `FreeSpinOutro.svelte:63,70`, `PressToContinue.svelte:19`).
- Malformed tags make `Intl` throw in `amount.ts`.
- The bad value is also sent to authenticate (`Authenticate.svelte:37`).
- Our own messages exist only for `en` and `zh` (`game\src\i18n\messagesMap\index.ts:8-11`).

## Steps
1. Add `game\web\seventh-veil\src\overrides\safeLang.ts`. It exports `safeLang(raw)`, which returns the value if it is in our supported list and `'en'` otherwise.
2. Support only `en` at launch. Keep `zh` only if every text has a translation. Reviewers test English.
3. Use `safeLang()` in our `Authenticate.svelte` and in a local copy of `LoadI18n.svelte`. Use a Vite transform on shared `stateUrl` if other shared code reads `lang`.
4. Until task 16 replaces the sprite text with font text through `t()`, map every locale to the `_en` sprite frame.

## Done test
- Demo play with `?lang=xx`, `?lang=en_US` and `?lang=` (empty): English text, no console errors, layout intact.
- Open every screen with `?lang=en`. No raw keys, `undefined` or `NaN` appear.
