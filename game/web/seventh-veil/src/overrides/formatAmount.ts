// Money formatting for every currency the RGS can send (Engine guidelines [219], [273], [78]).
// No imports, so scripts/check_amount.ts can run it with `node --experimental-strip-types`.
//
// Rules (studio.engine.io/docs-content/prompt.md, "Currency display", 2026-10-28):
// - USD $10.00, EUR €10.00, CAD CA$10.00, MXN MX$10.00, JPY ¥10 (0 decimals).
// - Social coins: XSC and XEC show as "10.00 SC", XGC as "10.00 GC", never with "$".
// - Sub-cent amounts keep their digits (0.004 -> $0.004), up to MAX_FRACTION_DIGITS.
// - Codes Intl does not know (USDT, DOGE) or a bad locale must not throw.

const SOCIAL_COIN_LABELS: Record<string, string> = {
	XSC: 'SC',
	XEC: 'SC',
	XGC: 'GC',
};

const MAX_FRACTION_DIGITS = 4;
const DEFAULT_FRACTION_DIGITS = 2;

// Fraction digits needed to show `value` exactly, between `min` and MAX_FRACTION_DIGITS.
const fractionDigitsFor = (value: number, min: number) => {
	for (let digits = min; digits < MAX_FRACTION_DIGITS; digits++) {
		const scaled = Math.abs(value) * 10 ** digits;
		if (Math.abs(scaled - Math.round(scaled)) < 1e-6) return digits;
	}
	return MAX_FRACTION_DIGITS;
};

const currencyFractionDigits = (currency: string, locale: string) => {
	try {
		return new Intl.NumberFormat(locale, { style: 'currency', currency }).resolvedOptions()
			.maximumFractionDigits ?? DEFAULT_FRACTION_DIGITS;
	} catch {
		return DEFAULT_FRACTION_DIGITS;
	}
};

const formatPlain = (value: number, digits: number, locale: string) => {
	const options = { minimumFractionDigits: digits, maximumFractionDigits: digits };
	try {
		return new Intl.NumberFormat(locale, options).format(value);
	} catch {
		return new Intl.NumberFormat('en', options).format(value);
	}
};

export const formatAmount = (value: number, currency: string, locale = 'en') => {
	const code = (currency || 'USD').toUpperCase();

	if (code in SOCIAL_COIN_LABELS) {
		const digits = fractionDigitsFor(value, DEFAULT_FRACTION_DIGITS);
		return `${formatPlain(value, digits, locale)} ${SOCIAL_COIN_LABELS[code]}`;
	}

	const digits = fractionDigitsFor(value, currencyFractionDigits(code, locale));
	const options = {
		style: 'currency' as const,
		currency: code,
		minimumFractionDigits: digits,
		maximumFractionDigits: digits,
	};

	for (const tryLocale of [locale, 'en']) {
		try {
			return new Intl.NumberFormat(tryLocale, options).format(value);
		} catch {
			// unknown locale or non-ISO currency code: try the next option
		}
	}

	// Non-ISO code such as USDT: number with the code as a suffix.
	return `${formatPlain(value, digits, locale)} ${code}`;
};
