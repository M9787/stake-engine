# Seventh Veil (math)

7x7 cluster-pays tumble game with a charged multiplier grid. Clusters of 5+ pay and explode.
A win on an empty spot marks it; the next win charges it to x2; each later win doubles it up to x1024.
Cluster pay is multiplied by the sum of charged spots under it.

Every pay is at least 1.2x, so every hit beats the stake. L4 appears only on bonus reels.
Base game: grid resets every spin. 3-4 scatters -> Star bonus, 5+ -> Tower bonus.
Bonus: grid persists for the whole bonus. Tower starts with 12 spots at x2, Star with 5 spots at x2. 3+ scatters retrigger +5 spins.
Buy floor: bought Star bonuses never pay below 10x, Tower below 40x (results under the floor are re-simulated).

Modes: base (1x), omen (1.25x), prophecy (2x) - same rules, more frequent bonuses;
star (100x buy), tower (400x buy). RTP 0.965 in all modes. Max win 77,777x.

Source of truth: stake\game\math\seventh_veil. Edit there, then run stake\scripts\sync.ps1.
