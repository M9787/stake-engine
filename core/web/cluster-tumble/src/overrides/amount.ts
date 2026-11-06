// Core replacement for web-sdk/packages/utils-shared/amount.ts (packages are read-only).
// vite.config.js aliases the specifier 'utils-shared/amount' here, so every shared label
// (balance, bet, win, bonus card prices) and our own components use the same formatter.
// Exports match the shared file one to one; only the money formatting changed (formatAmount.ts).
import { stateBet, stateI18n } from 'state-shared';

import { BOOK_AMOUNT_MULTIPLIER } from 'constants-shared/bet';

import { formatAmount } from './formatAmount';

export const bookEventAmountToBetAmountMultiplier = (bookEventAmount: number) =>
	bookEventAmount / BOOK_AMOUNT_MULTIPLIER;

export const bookEventAmountToNormalisedAmount = (bookEventAmount: number) => {
	const betAmountMultiplier = bookEventAmountToBetAmountMultiplier(bookEventAmount);
	return stateBet.wageredBetAmount * betAmountMultiplier;
};

export const numberToFloat = (value: number) => Number.parseFloat(`${value}`);

export const numberToCurrencyString = (value: number) =>
	formatAmount(numberToFloat(value), stateBet.currency, stateI18n.i18n.locale || 'en');

export const bookEventAmountToCurrencyString = (bookEventAmount: number) => {
	const normalisedAmount = bookEventAmountToNormalisedAmount(bookEventAmount);
	return numberToCurrencyString(normalisedAmount);
};
