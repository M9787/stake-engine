# 12 — Back up the repo on GitHub (15 min)

**Why:** Today the project exists only on this PC. A disk failure would lose months of work (PROJECT.md Q2).

## Steps
1. Go to https://github.com/new.
2. Name: `oracle-of-sevens`. Choose **Private**. Do not add a README.
3. Click **Create repository** and copy the URL (it ends in `.git`).
4. Tell the agent: "push to <URL>". The agent will:
   - check that `.env` and secrets are not included;
   - ask you about Git LFS for big art files;
   - push the `master` branch.

## Done when
- The repo page on GitHub shows the project files.
