# 06 — Upload and publish files in Studio (30 min)

**Why:** Reviewers can only see what is published. Readiness needs "Math version published" and "Front version published".

**Wait for:** the agent says "ready for upload" (agent task 21).

## Steps
1. Open https://studio.engine.io/teams/dumalex/games/oracle-of-sevens/files.
2. **Math first:**
   1. Click **Import Files**.
   2. Select the folder `C:\Users\User\Desktop\Claude Code\stake\math-sdk\games\seventh_veil\library\publish_files`.
   3. Click **Start Sync** and wait until it finishes. The files are about 1 GB, so it can take a while.
3. **Front end:**
   1. Click **Import Files**.
   2. Select `C:\Users\User\Desktop\Claude Code\stake\upload\front`.
   3. Click **Start Sync**.
4. Publish the math version, then the front version. The buttons are on the Files page.
5. Open **Start Approval** and check that these are green:
   - Math version published;
   - Front version published;
   - Math validation;
   - Betlevel validation.
6. If anything is red, copy the exact message to the agent.

## Done when
- All four checks above are green. Tell the agent "uploaded", so it can run the staging test (agent task 22).

**Note:** each later fix needs a new upload and publish. Reviewers see only the latest published version.
