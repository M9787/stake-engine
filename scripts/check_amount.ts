// check_amount.ts - checks money formatting against the Engine currency table and fails on wrong output.
// Source: stake-engine.com/docs/rgs "Supported currencies" (Example column, 2026-11-06), plus
// "Minimum bet sizes" (sub-cent wins keep exact digits) and Engine [78] (SC/GC, never "$").
// Usage: node --experimental-strip-types scripts\check_amount.ts
// Exit code: 0 = all good, 1 = at least one wrong value.

import { CURRENCY_META, formatAmount } from '../core/web/cluster-tumble/src/overrides/formatAmount.ts';

// Engine "Example" column for 10 units, one row per currency (en locale, no grouping at 10).
const ENGINE_EXAMPLES: Record<string, string> = {
	USD: '$10.00', CAD: 'CA$10.00', JPY: '¥10', EUR: '€10.00', RUB: '₽10.00', CNY: 'CN¥10.00',
	PHP: '₱10.00', INR: '₹10.00', IDR: 'Rp10', KRW: '₩10', BRL: 'R$10.00', MXN: 'MX$10.00',
	DKK: '10.00 kr', PLN: '10.00 zł', VND: '10 ₫', TRY: '₺10.00', CLP: '10 CLP', ARS: '10.00 ARS',
	PEN: 'S/10.00', NGN: '₦10.00', SAR: '10.00 SAR', ILS: '₪10.00', AED: '10.00 AED', TWD: 'NT$10.00',
	NOK: '10.00 kr', KWD: 'KD10.000', JOD: 'JD10.000', CRC: '₡10.00', TND: '10.000 TND', SGD: 'SG$10.00',
	MYR: 'RM10.00', OMR: '10.000 OMR', QAR: '10.00 QAR', BHD: 'BD10.000', PKR: '₨10.00', EGP: '10.00 EGP',
	NZD: 'NZ$10.00', BOB: 'Bs10.00', GHS: 'GH₵10.00', KES: 'KSh10.00', MAD: '10.00 MAD', BAM: 'KM10.00',
	ISK: '10 kr', TZS: 'TSh10.00', UGX: 'USh10', XOF: '10 CFA', AUD: 'A$10.00', BWP: 'P10.00',
	GEL: '₾10.00', HNL: 'L10.00', JMD: 'J$10.00', KGS: '10.00 KGS', MZN: '10.00 MZN', PGK: 'K10.00',
	TMT: '10.00 TMT', TTD: 'TT$10.00', UAH: '₴10.00', XCD: 'EC$10.00', APE: '10.0000 APE',
	BCH: '10.000000 BCH', BNB: '10.000000 BNB', BTC: '10.000000 BTC', BUSD: '10.00 BUSD',
	CRO: '10.0000 CRO', DAI: '10.00 DAI', DOGE: '10.0000 DOGE', EOS: '10.0000 EOS', ETH: '10.000000 ETH',
	LINK: '10.0000 LINK', LTC: '10.000000 LTC', POL: '10.0000 POL', SAND: '10.0000 SAND', SHIB: '10 SHIB',
	SOL: '10.000000 SOL', TRUMP: '10.0000 TRUMP', TRX: '10.0000 TRX', UNI: '10.0000 UNI',
	USDC: '10.00 USDC', USDT: '10.00 USDT', XRP: '10.0000 XRP', XGC: '10.00 GC', XSC: '10.00 SC',
	XEC: '10.00 SC', XRC: '10.00 SC', WRW: '10.00 SC',
};

// Extra cases: sub-cent wins, grouping, unknown code, negative, lower-case code.
const EXTRA: [number, string, string][] = [
	[0.001, 'USD', '$0.001'], // 0.1x win on a $0.01 bet
	[0.004, 'USD', '$0.004'],
	[0.012, 'USD', '$0.012'],
	[0.0012, 'EUR', '€0.0012'],
	[0.004, 'XSC', '0.004 SC'],
	[0.5, 'JPY', '¥0.5'], // exact value kept, never rounded to ¥1 / ¥0
	[1234.5, 'USD', '$1,234.50'],
	[10, 'ABC', '10.00 ABC'], // unknown code: Engine fallback
	[-1, 'USD', '-$1.00'],
	[-1, 'DKK', '-1.00 kr'],
	[10, 'usdt', '10.00 USDT'],
];

let failed = 0;
const check = (value: number, currency: string, expected: string) => {
	let text: string;
	try {
		text = formatAmount(value, currency, 'en');
	} catch (error) {
		text = `THROWS ${error}`;
	}
	const social = ['XSC', 'XEC', 'XGC', 'XRC', 'WRW'].includes(currency.toUpperCase());
	const bad = text !== expected || (social && text.includes('$'));
	if (bad) {
		failed++;
		console.log(`FAIL ${currency} ${value}: got "${text}", want "${expected}"`);
	}
};

const missing = Object.keys(ENGINE_EXAMPLES).filter((code) => !(code in CURRENCY_META));
if (missing.length) {
	failed += missing.length;
	console.log(`FAIL not in CURRENCY_META: ${missing.join(', ')}`);
}
for (const [code, expected] of Object.entries(ENGINE_EXAMPLES)) check(10, code, expected);
for (const [value, code, expected] of EXTRA) check(value, code, expected);

// Bad locale must fall back, not throw.
try {
	formatAmount(1, 'EUR', 'en_US');
} catch (error) {
	failed++;
	console.log(`FAIL bad locale en_US throws: ${error}`);
}

const total = Object.keys(ENGINE_EXAMPLES).length + EXTRA.length + 1;
console.log(failed ? `FAIL ${failed} of ${total} checks` : `OK all ${total} checks (${Object.keys(ENGINE_EXAMPLES).length} Engine currencies)`);
process.exit(failed ? 1 : 0);
