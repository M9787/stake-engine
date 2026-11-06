// Money formatting for every currency the RGS can send (Engine guidelines [219], [273], [78]).
// No imports, so scripts/check_amount.ts can run it with `node --experimental-strip-types`.
//
// Source: stake-engine.com/docs/rgs "Supported currencies" + CurrencyMeta helper (2026-11-06).
// - Symbol, default decimals and placement come from CURRENCY_META (Engine table, verbatim).
// - Unknown codes: 2 decimals, code after the amount (Engine fallback).
// - Never pass the code to Intl `style: 'currency'`: it throws for non-3-letter codes (USDT, TRUMP).
// - Wins keep exact digits for small bets (0.1x * $0.01 = $0.001), up to the RGS precision of
//   6 decimals ("Minimum bet sizes"). Values that need no extra digits show the default decimals.

type Meta = { symbol: string; decimals: number; symbolAfter?: boolean };

export const CURRENCY_META: Record<string, Meta> = {
	USD: { symbol: '$', decimals: 2 },
	CAD: { symbol: 'CA$', decimals: 2 },
	JPY: { symbol: '¥', decimals: 0 },
	EUR: { symbol: '€', decimals: 2 },
	RUB: { symbol: '₽', decimals: 2 },
	CNY: { symbol: 'CN¥', decimals: 2 },
	PHP: { symbol: '₱', decimals: 2 },
	INR: { symbol: '₹', decimals: 2 },
	IDR: { symbol: 'Rp', decimals: 0 },
	KRW: { symbol: '₩', decimals: 0 },
	BRL: { symbol: 'R$', decimals: 2 },
	MXN: { symbol: 'MX$', decimals: 2 },
	DKK: { symbol: 'kr', decimals: 2, symbolAfter: true },
	PLN: { symbol: 'zł', decimals: 2, symbolAfter: true },
	VND: { symbol: '₫', decimals: 0, symbolAfter: true },
	TRY: { symbol: '₺', decimals: 2 },
	CLP: { symbol: 'CLP', decimals: 0, symbolAfter: true },
	ARS: { symbol: 'ARS', decimals: 2, symbolAfter: true },
	PEN: { symbol: 'S/', decimals: 2 },
	NGN: { symbol: '₦', decimals: 2 },
	SAR: { symbol: 'SAR', decimals: 2, symbolAfter: true },
	ILS: { symbol: '₪', decimals: 2 },
	AED: { symbol: 'AED', decimals: 2, symbolAfter: true },
	TWD: { symbol: 'NT$', decimals: 2 },
	NOK: { symbol: 'kr', decimals: 2, symbolAfter: true },
	KWD: { symbol: 'KD', decimals: 3 },
	JOD: { symbol: 'JD', decimals: 3 },
	CRC: { symbol: '₡', decimals: 2 },
	TND: { symbol: 'TND', decimals: 3, symbolAfter: true },
	SGD: { symbol: 'SG$', decimals: 2 },
	MYR: { symbol: 'RM', decimals: 2 },
	OMR: { symbol: 'OMR', decimals: 3, symbolAfter: true },
	QAR: { symbol: 'QAR', decimals: 2, symbolAfter: true },
	BHD: { symbol: 'BD', decimals: 3 },
	PKR: { symbol: '₨', decimals: 2 },
	EGP: { symbol: 'EGP', decimals: 2, symbolAfter: true },
	NZD: { symbol: 'NZ$', decimals: 2 },
	BOB: { symbol: 'Bs', decimals: 2 },
	GHS: { symbol: 'GH₵', decimals: 2 },
	KES: { symbol: 'KSh', decimals: 2 },
	MAD: { symbol: 'MAD', decimals: 2, symbolAfter: true },
	BAM: { symbol: 'KM', decimals: 2 },
	ISK: { symbol: 'kr', decimals: 0, symbolAfter: true },
	TZS: { symbol: 'TSh', decimals: 2 },
	UGX: { symbol: 'USh', decimals: 0 },
	XOF: { symbol: 'CFA', decimals: 0, symbolAfter: true },
	AUD: { symbol: 'A$', decimals: 2 },
	BWP: { symbol: 'P', decimals: 2 },
	GEL: { symbol: '₾', decimals: 2 },
	HNL: { symbol: 'L', decimals: 2 },
	JMD: { symbol: 'J$', decimals: 2 },
	KGS: { symbol: 'KGS', decimals: 2, symbolAfter: true },
	MZN: { symbol: 'MZN', decimals: 2, symbolAfter: true },
	PGK: { symbol: 'K', decimals: 2 },
	TMT: { symbol: 'TMT', decimals: 2, symbolAfter: true },
	TTD: { symbol: 'TT$', decimals: 2 },
	UAH: { symbol: '₴', decimals: 2 },
	XCD: { symbol: 'EC$', decimals: 2 },
	APE: { symbol: 'APE', decimals: 4, symbolAfter: true },
	BCH: { symbol: 'BCH', decimals: 6, symbolAfter: true },
	BNB: { symbol: 'BNB', decimals: 6, symbolAfter: true },
	BTC: { symbol: 'BTC', decimals: 6, symbolAfter: true },
	BUSD: { symbol: 'BUSD', decimals: 2, symbolAfter: true },
	CRO: { symbol: 'CRO', decimals: 4, symbolAfter: true },
	DAI: { symbol: 'DAI', decimals: 2, symbolAfter: true },
	DOGE: { symbol: 'DOGE', decimals: 4, symbolAfter: true },
	EOS: { symbol: 'EOS', decimals: 4, symbolAfter: true },
	ETH: { symbol: 'ETH', decimals: 6, symbolAfter: true },
	LINK: { symbol: 'LINK', decimals: 4, symbolAfter: true },
	LTC: { symbol: 'LTC', decimals: 6, symbolAfter: true },
	POL: { symbol: 'POL', decimals: 4, symbolAfter: true },
	SAND: { symbol: 'SAND', decimals: 4, symbolAfter: true },
	SHIB: { symbol: 'SHIB', decimals: 0, symbolAfter: true },
	SOL: { symbol: 'SOL', decimals: 6, symbolAfter: true },
	TRUMP: { symbol: 'TRUMP', decimals: 4, symbolAfter: true },
	TRX: { symbol: 'TRX', decimals: 4, symbolAfter: true },
	UNI: { symbol: 'UNI', decimals: 4, symbolAfter: true },
	USDC: { symbol: 'USDC', decimals: 2, symbolAfter: true },
	USDT: { symbol: 'USDT', decimals: 2, symbolAfter: true },
	XRP: { symbol: 'XRP', decimals: 4, symbolAfter: true },
	XGC: { symbol: 'GC', decimals: 2, symbolAfter: true },
	XSC: { symbol: 'SC', decimals: 2, symbolAfter: true },
	XEC: { symbol: 'SC', decimals: 2, symbolAfter: true },
	XRC: { symbol: 'SC', decimals: 2, symbolAfter: true },
	WRW: { symbol: 'SC', decimals: 2, symbolAfter: true },
};

// RGS amounts carry six decimal places, so no value needs more.
const MAX_FRACTION_DIGITS = 6;

export const currencyMeta = (currency: string): Meta => {
	const code = (currency || 'USD').toUpperCase();
	return CURRENCY_META[code] ?? { symbol: code, decimals: 2, symbolAfter: true };
};

// Fraction digits needed to show `value` exactly, between `min` and MAX_FRACTION_DIGITS.
const fractionDigitsFor = (value: number, min: number) => {
	for (let digits = min; digits < MAX_FRACTION_DIGITS; digits++) {
		const scaled = Math.abs(value) * 10 ** digits;
		if (Math.abs(scaled - Math.round(scaled)) < 1e-6) return digits;
	}
	return MAX_FRACTION_DIGITS;
};

const formatNumber = (value: number, digits: number, locale: string) => {
	const options = { minimumFractionDigits: digits, maximumFractionDigits: digits };
	for (const tryLocale of [locale, 'en']) {
		try {
			return new Intl.NumberFormat(tryLocale, options).format(value);
		} catch {
			// bad locale string such as en_US: try the next option
		}
	}
	return value.toFixed(digits);
};

export const formatAmount = (value: number, currency: string, locale = 'en') => {
	const meta = currencyMeta(currency);
	const digits = fractionDigitsFor(value, meta.decimals);
	// Sign goes before the symbol (net position can be negative): -$1.00, -1.00 kr.
	const sign = value < 0 ? '-' : '';
	const number = formatNumber(Math.abs(value), digits, locale);
	return meta.symbolAfter ? `${sign}${number} ${meta.symbol}` : `${sign}${meta.symbol}${number}`;
};
