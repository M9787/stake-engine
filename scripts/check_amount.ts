// check_amount.ts - prints money formatting for every test currency and fails on wrong output.
// Covers Engine guidelines [219] (symbol, decimals), [273] (sub-cent) and [78] (SC/GC, no "$").
// Usage: node --experimental-strip-types scripts\check_amount.ts
// Exit code: 0 = all good, 1 = at least one wrong value.

import { formatAmount } from '../game/web/seventh-veil/src/overrides/formatAmount.ts';

const CURRENCIES = ['USD', 'EUR', 'CAD', 'MXN', 'JPY', 'XSC', 'XGC', 'XEC', 'USDT'];
const VALUES = [0.004, 0.012, 1, 1234.5];

// Exact strings from the prompt's currency table (en locale).
const EXPECTED: Record<string, string> = {
	'USD 1': '$1.00',
	'EUR 1': '€1.00',
	'CAD 1': 'CA$1.00',
	'MXN 1': 'MX$1.00',
	'JPY 1': '¥1',
	'XSC 1': '1.00 SC',
	'XGC 1': '1.00 GC',
	'XEC 1': '1.00 SC',
	'USD 0.004': '$0.004',
	'USD 0.012': '$0.012',
	'XSC 0.004': '0.004 SC',
};

let failed = 0;
for (const currency of CURRENCIES) {
	const row: string[] = [];
	for (const value of VALUES) {
		let text: string;
		try {
			text = formatAmount(value, currency, 'en');
		} catch (error) {
			text = `THROWS ${error}`;
		}
		const expected = EXPECTED[`${currency} ${value}`];
		// Every sub-cent value must keep its digits (JPY included: no rounding to 0).
		const subCentRounded = value < 0.01 && !text.includes('0.004');
		const socialDollar = currency.startsWith('X') && text.includes('$');
		const bad = text.startsWith('THROWS') || subCentRounded || socialDollar || (expected && text !== expected);
		if (bad) failed++;
		row.push(`${bad ? 'FAIL ' : ''}${text}`);
	}
	console.log(`${currency.padEnd(5)} ${row.join(' | ')}`);
}

// Bad locale must fall back, not throw.
try {
	formatAmount(1, 'EUR', 'en_US');
	console.log('bad locale en_US: ok');
} catch (error) {
	failed++;
	console.log(`FAIL bad locale en_US throws: ${error}`);
}

console.log(failed ? `FAIL ${failed} value(s)` : 'OK all values');
process.exit(failed ? 1 : 0);
