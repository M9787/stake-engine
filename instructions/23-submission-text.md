# 23 — Submission text

**Goal:** Have every text field for the Studio submission tabs ready to paste.

**Why:**
- Approval needs "a short blurb".
- The title must be unique and free of restricted terms ([213]).
- Clear reviewer notes cut feedback rounds. One open review only until the first game is live, so each round costs days.

**Depends on:** 22.

## Steps
1. Write `docs\submission.md` with:
   - **Blurb:** 2 short paragraphs of theme and mechanic, no claims about winning;
   - **Feature list:** 7x7 clusters, tumble, charged multiplier grid up to x1024, Star and Tower bonuses, 3 Fates, 77,777x max;
   - **Per-mode table:** cost, RTP and max win, copied from docs/07;
   - **Reviewer notes:** how to reach each bonus quickly (forced books in storybook, if allowed), known limits, test currencies;
   - **Compliance answers:** the stateless design, no jackpots, original art, the `ASSET_LICENSES.md` summary.
2. Title check:
   - search the web for "Oracle of Sevens" slot;
   - ask the user to search the Stake lobby (human task 09);
   - check restricted words in the title.
3. Tarot theme risk (Q7): note in the reviewer notes that the art uses original designs, no real deck art and no religious symbols.

## Done test
- `docs\submission.md` covers every field on the Payment, Distribution, Compliance and Details tabs. Read the field names live from Studio with the user's OK.
