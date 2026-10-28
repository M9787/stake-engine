# 08 — Replay

**Goal:**
- A replay URL loads and plays the event with no wallet calls.
- It uses `currency`, `lang` and `amount`, and survives invalid values.
- It can be played again.
- It shows the bet, the mode multiplier and the real cost.
- It works at 400×225.

**Why:** Guidelines [171], [172], [173], [174], [243] (https://studio.engine.io/docs-content/prompt.md, 2026-10-28). Real cost = `amount × costMultiplier`.

**Depends on:** 03 (currency format), 05 (lang).

## Current problems (audit 2026-10-28)
- Replay never reads `currency`. See `game\...\Authenticate.svelte:136-161`, and `stateUrl.svelte.ts:11` lists `currency` with no accessor. It defaults to USD.
- `game\src\components\ui\UI.svelte:22` uses the shared `UIReplay`, which has no Play-again button.
- `LabelBet.svelte:17` shows `betCost()`, which multiplies only `activate` modes. So Star and Tower replays show 1x instead of 100x and 400x.
- `UIReplay.svelte` mounts `EnableSpaceHold` without the jurisdiction guard that our `UIDefault.svelte:53` has.

## Steps
1. In our `Authenticate.svelte` replay branch, read `currency`, `lang` and `amount` from the URL. Pass them through `safeLang()` (task 05) and the currency formatter (task 03). Use defaults on bad values.
2. Make a local `UIReplay.svelte` and point `UI.svelte:22` at it. It:
   - shows "Bet {amount}", "Mode {name} ×{cost}" and "Cost {amount×cost}";
   - adds a "Replay again" button that restarts the same event;
   - has no space-hold and no route into real play.
3. Fix the cost shown for buy modes: either a local `LabelBet`, or the same `stateBet` transform from task 06.
4. Test with the mock `/bet/replay`. Use one replay URL per mode, including tower, with `&currency=EUR&lang=en&amount=2000000`.

## Done test
- The Tower replay shows bet 2.00, ×400 and cost 800.00 in EUR.
- "Replay again" works twice in a row.
- The Network tab shows no `/wallet/*` calls during replay.
- At 400×225 the replay is readable and usable. Save the screenshot to `docs\screens\replay-400x225.png`.
