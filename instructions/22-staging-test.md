# 22 — Staging test on Studio

**Goal:** The real RGS behaves like our mock in every mode, before reviewers see the game.

**Why:**
- Reviewers play every submission.
- Open questions Q5, Q9, Q11, Q12 and Q13 (PROJECT.md §11) can only be answered on the real RGS.

**Depends on:** 21, and human task 06 (files uploaded and published).

## Steps
Use the user's Chrome only with their OK, for read-only play on the Studio "Play Game" button. Never click Submit, Publish or Upload.
1. Open the game from Studio → Oracle of Sevens → Play Game.
2. Play 1 round per mode: base, omen, prophecy, star, tower. Write down the balance before and after.
   - Q11: does the RGS charge `amount × cost` for buys?
   - Q9: is the mode-name case OK?
3. Checks (guideline IDs from the AI review prompt):
   - [242]: bet levels come from authenticate;
   - [187]: reload during a bonus resumes the round with its own bet;
   - [221]: a losing round sends no end-round;
   - [222]: no play request at zero balance;
   - [274]: a bad `rgs_url` shows an error.
4. Add `&social=true` and check the labels (Q12).
5. Check replay: does Engine provide a replay link (Q5)?
6. Test at 1024×576, 400×225, 800×450 and 425×812.
7. Watch for the $10 vs $1 bet glitch (Q13).
8. Update PROJECT.md §11 with the answers. Note the evidence (screenshot or network log) in `docs\staging-2026-MM-DD.md`.

## Done test
- Every check passes, or has its own fix task.
- Q5, Q9, Q11, Q12 and Q13 are each closed or updated with evidence.
