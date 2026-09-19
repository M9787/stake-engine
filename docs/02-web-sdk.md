# 02 — Web SDK (Svelte + PixiJS side)

## Purpose

Run and build the `seventh-veil` app (forked from `apps/cluster`). Source lives in `game\web\seventh-veil`.

## Prereq

- Node and pnpm per [PROJECT.md §3](../PROJECT.md#3-stack-pinned). Check: `scripts\doctor.ps1`.
- web-sdk cloned to `stake\web-sdk`, `pnpm install` done (needs network once).
- Math built ([01](01-math-sdk.md)).

## Steps

Edit only `game\web\seventh-veil\`, then copy it into the workspace:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync.ps1
math-sdk\env\Scripts\python.exe scripts\gen_fe_config.py      # math config_fe -> src\game\config.ts
math-sdk\env\Scripts\python.exe scripts\books_to_stories.py   # books -> stories + contract check
```

Placeholder art (dev only, untracked, rejected at review): copy `web-sdk\apps\cluster\static` to `web-sdk\apps\seventh-veil\static` once.

| File (in `src\`) | Owns |
|---|---|
| `game\config.ts` | generated from math; do not edit |
| `game\betModes.ts` | 5 bet modes for the shared UI (BASE, OMEN, PROPHECY, STAR, TOWER); celebration gate |
| `game\bookEventHandlerMap.ts` | book events → emitter events, incl. `bonusVariant`, `wincap` |
| `components\GameModals.svelte`, `GameInfo.svelte` | modal set with our pay table and rules (RTP, cost, max win per mode) |
| `components\EnableJurisdiction.svelte` | backstop: reverts turbo / autoplay / buy mode when the jurisdiction disables them |
| `components\ui\UI.svelte`, `UIDefault.svelte`, `ButtonBet.svelte` | copies of `components-ui-pixi` (deep imports): hide turbo / autoplay / buy buttons per jurisdiction; Space respects `disabledSpacebar` |
| `components\Authenticate.svelte` | copy of `components-shared` Authenticate: `defaultBetLevel`, bet-level fallback, `social=true`, replay error message |
| `components\ModalError.svelte` | RGS error code → player message, never raw JSON |
| `game\wording.ts` | social-casino wording (`t()`), from the Engine restricted-terms list |
| `assets\fonts\` | Inter (SIL OFL) registered as `proxima-nova`; replaces Typekit |
| `stubs\webfontloader.js` | aliased in `vite.config.js`; waits for bundled fonts, no Typekit request |
| `..\dev\mockRgs.js` | local mock RGS (dev server only, never built) |
| `stories\Mode*`, `stories\data\*` | generated from books; do not edit |

Run:

```powershell
cd web-sdk\apps\seventh-veil; pnpm run storybook    # port 6007, replays books, no RGS needed
cd web-sdk; pnpm run dev --filter=seventh-veil      # port 3007, needs a real RGS session query string (PROJECT.md §7)
cd web-sdk; pnpm run build --filter=seventh-veil    # output: apps\seventh-veil\.svelte-kit\output\
```

### Demo play (local mock RGS)

Real spins with a demo balance, no Stake Engine account needed. The mock serves the real books, drawn by lookup weight.

```powershell
math-sdk\env\Scripts\python.exe scripts\books_to_mock.py            # .mock-rgs\<mode>.json (after every math change)
powershell -ExecutionPolicy Bypass -File scripts\dev_cert.ps1       # self-signed cert; the SDK always calls https://{rgs_url}
cd web-sdk\apps\seventh-veil; pnpm run dev:demo
# open https://localhost:3007/?sessionID=demo&rgs_url=localhost:3007/rgs&lang=en  (accept the certificate once)
```

`sessionID` tokens set demo conditions: `demo_b5` (start with $5), `demo_social`, `demo_nobuy`, `demo_noturbo`, `demo_noauto`, `demo_nospace`. Force the next round: `POST https://localhost:3007/rgs/mock/force` with `{"sessionID":"demo","next":"maxwin"}` (or `"bonus"`). Replay a demo round: `?replay=true&game=seventh_veil&version=1&mode=BASE&event=<roundID>&amount=1000000&rgs_url=localhost:3007/rgs`. Contract: [03](03-contract.md#mock-rgs).

The storybook script sets `PUBLIC_CHROMATIC=true` through a small `node -e` wrapper, so it runs on Windows. Vite may not exit after the build finishes; the output is complete once `index.html` exists.

## Verify

- Storybook: MODE_BASE / MODE_STAR / MODE_TOWER stories play (verified 2026-09-19: base `bonus_star` book reaches 12 free spins with grid marks).
- Build leaves `prerendered\pages\index.html` and `client\` in `apps\seventh-veil\.svelte-kit\output\`.
- `scripts\check_external_urls.ps1` exits 0 on that output.
- Demo play: one round per mode completes and the balance changes by payout − bet × mode cost.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://github.com/engineio/web-sdk | commands, apps/packages layout, build output path | 2026-09-19 |
| https://raw.githubusercontent.com/engineio/web-sdk/main/apps/cluster/package.json | cluster app scripts and ports | 2026-09-19 |
