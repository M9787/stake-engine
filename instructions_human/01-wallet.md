# 01 — Add your payout wallet

**Why:** Engine pays on the 1st of each month in USDT or USDC to an ERC-20 wallet. With no wallet, your balance waits for the next month. If you add a new wallet later, it waits 3 days before it is active. Source: https://studio.engine.io/docs/payments (2026-10-28).

## Steps
1. Use a wallet that **you** control (for example MetaMask, or a hardware wallet). Do not use an exchange deposit address unless the exchange says ERC-20 USDT/USDC deposits are supported.
2. Copy your ERC-20 address. It starts with `0x`.
3. Open https://studio.engine.io/teams/dumalex/wallet.
4. Paste the address, choose USDT or USDC, and fill in the address fields it asks for.
5. Check the first 4 and last 4 characters twice. A wrong address means lost money.
6. Save.

## Done when
- The Wallet page shows your address. Tell the agent "wallet done".

**Never paste your seed phrase or private key anywhere, and never give it to the agent.**
