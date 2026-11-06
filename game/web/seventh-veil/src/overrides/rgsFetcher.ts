// Seventh Veil replacement for web-sdk/packages/rgs-fetcher (packages are read-only).
// vite.config.js aliases the specifier 'rgs-fetcher' here. Same export and call shape.
//
// Why: the shared fetcher calls response.json() on every response. Engine also answers with
// non-JSON bodies (stake-engine.com/docs/rgs/wallet "Response codes", 2026-11-06):
// - 400 plain "Bad Request" (malformed body or sessionID)
// - 423 on /wallet/play: new bets paused (maintenance); balance and end-round still work
// - 429 on a demo launch: too many requests from the IP
// and 429 ERR_ACT ("retry shortly"). Every failure now resolves to { error: <code> } so the
// caller's `data?.error` check opens the error modal with a player message, never raw JSON.

// Same request as utils-fetcher (not a dependency of this app): JSON body on POST.
const fetcher = (options: { method: 'POST' | 'GET'; endpoint: string; variables?: object }) =>
	fetch(options.endpoint, {
		method: options.method,
		headers: { 'Content-Type': 'application/json' },
		...(options.method === 'GET' ? {} : { body: JSON.stringify(options.variables) }),
	});

export type RgsError = { error: string; message?: string; status?: number };

// ERR_ACT: the provably fair draw was not taken, so nothing was debited; retrying is safe.
const RETRY_DELAYS_MS = [400, 1000, 2000];

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const statusToCode = (status: number) => {
	if (status === 423) return 'ERR_PAUSED';
	if (status === 429) return 'ERR_RATE';
	if (status === 400) return 'ERR_BAD_REQUEST';
	if (status === 404) return 'ERR_NOT_FOUND';
	return 'ERR_GEN';
};

const readBody = async (response: Response): Promise<unknown> => {
	const text = await response.text();
	if (!text) return null;
	try {
		return JSON.parse(text);
	} catch {
		return null;
	}
};

const request = async (options: { method: 'POST' | 'GET'; endpoint: string; variables?: object }) => {
	for (let attempt = 0; ; attempt++) {
		let response: Response;
		try {
			response = await fetcher(options);
		} catch {
			return { error: 'ERR_NETWORK' } satisfies RgsError;
		}

		const body = (await readBody(response)) as { error?: unknown } | null;
		if (response.ok && body) return body;

		const code =
			body && typeof body.error === 'string' ? body.error : statusToCode(response.ok ? 500 : response.status);
		if (code === 'ERR_ACT' && attempt < RETRY_DELAYS_MS.length) {
			await wait(RETRY_DELAYS_MS[attempt]);
			continue;
		}
		return { ...(body ?? {}), error: code, status: response.status } as RgsError;
	}
};

export const rgsFetcher = {
	post: async function post<TResponse = any>(options: {
		url: string;
		rgsUrl: string;
		variables?: object;
	}): Promise<TResponse> {
		return (await request({
			method: 'POST',
			variables: options.variables,
			endpoint: `https://${options.rgsUrl}${options.url}`,
		})) as TResponse;
	},
	get: async function get<TResponse = any>(options: { url: string; rgsUrl: string }): Promise<TResponse> {
		return (await request({ method: 'GET', endpoint: `https://${options.rgsUrl}${options.url}` })) as TResponse;
	},
};
